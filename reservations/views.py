from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.http import JsonResponse
from hotels.forms import GuestForm
from reservations.models import Booking, Guest, Transaction
from django.conf import settings
from django.views.generic import View, DetailView, TemplateView
from hotels.models import Room
import jdatetime
import json
import requests
from django.urls import reverse
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin

if settings.SANDBOX:
    sandbox = 'sandbox'
else:
    sandbox = 'payment'

ZP_API_REQUEST = f"https://{sandbox}.zarinpal.com/pg/v4/payment/request.json"
ZP_API_STARTPAY = f"https://{sandbox}.zarinpal.com/pg/StartPay/"
ZP_API_VERIFY = f"https://{sandbox}.zarinpal.com/pg/v4/payment/verify.json"
description = "رزرو اتاق در هتل ما"


class SendRequestView(LoginRequiredMixin, View):

    def post(self, request, slug):
        room = get_object_or_404(Room, slug=slug)

        capacity = int(request.POST.get('capacity', 0))
        check_in_str = request.POST.get('check_in')
        check_out_str = request.POST.get('check_out')
        errors = {}

        # اعتبارسنجی تاریخ‌ها
        try:
            check_in_jalali = jdatetime.datetime.strptime(check_in_str, '%Y/%m/%d').date()
            check_out_jalali = jdatetime.datetime.strptime(check_out_str, '%Y/%m/%d').date()
            if check_out_jalali <= check_in_jalali:
                errors['dates'] = 'تاریخ خروج باید بعد از تاریخ ورود باشد.'
            nights = (check_out_jalali - check_in_jalali).days
            if nights < 1:
                errors['dates'] = 'حداقل یک شب اقامت لازم است.'
        except (ValueError, TypeError):
            errors['dates'] = 'فرمت تاریخ‌ها نامعتبر است.'
            nights = 0

        if capacity != room.capacity:
            errors['capacity'] = 'تعداد مهمان‌ها با ظرفیت اتاق مطابقت ندارد.'

        guest_forms = [GuestForm(request.POST, prefix=f'guest_{i}') for i in range(1, capacity + 1)]
        guests_data = []
        is_guest_forms_valid = all(form.is_valid() for form in guest_forms)

        if not is_guest_forms_valid:
            errors['guests'] = 'اطلاعات حداقل یک مهمان نادرست یا ناقص است.'
        else:
            for form in guest_forms:
                guest_info = {key: str(value) for key, value in form.cleaned_data.items()}
                guests_data.append(guest_info)

        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        check_in_gregorian = check_in_jalali.togregorian()
        check_out_gregorian = check_out_jalali.togregorian()

        if Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out_gregorian,
                check_out__gt=check_in_gregorian
        ).exists():
            return HttpResponse('متاسفانه این اتاق در همین لحظه توسط شخص دیگری رزرو شد.', status=409)

        #  ذخیره اطلاعات نهایی در Session
        total_price = room.price * nights
        request.session['reservation_data'] = {
            'room_slug': slug,
            'check_in': check_in_jalali.isoformat(),
            'check_out': check_out_jalali.isoformat(),
            'capacity': capacity,
            'total_price': total_price,
            'guests': guests_data,
            "nights": nights
        }

        #  ارسال به درگاه پرداخت
        callback_url = request.build_absolute_uri(reverse('reservations:payment-verify'))
        data = {
            "merchant_id": settings.MERCHANT,
            "amount": total_price * 10,  # تبدیل تومان به ریال
            "description": f"{description} برای اتاق {room.title}",
            "callback_url": callback_url,
            "metadata": {"mobile": request.user.phone, "email": request.user.email}
        }

        try:
            response = requests.post(ZP_API_REQUEST, data=json.dumps(data),
                                     headers={'content-type': 'application/json'})
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("data", {}).get('code') == 100:
                    authority = response_data['data']['authority']
                    request.session['authority'] = authority
                    if response_data.get("data", {}).get('code') == 100:
                        authority = response_data['data']['authority']
                        request.session['authority'] = authority
                        url = f"{ZP_API_STARTPAY}{authority}"

                        return JsonResponse({'success': True, 'redirect_url': url})
            error_message = response.json().get('errors', {}).get('message', 'خطا در ارتباط با درگاه پرداخت')
            return HttpResponse(error_message, status=400)
        except requests.RequestException:
            return HttpResponse(f'خطای شبکه، لطفا از اتصال اینترنت خود اطمینان حاصل کنید', status=500)


class VerifyView(LoginRequiredMixin, View):

    def get(self, request):
        payment_status = request.GET.get('Status')
        authority = request.GET.get('Authority')
        session_authority = request.session.get('authority')
        reservation_data = request.session.get('reservation_data')

        if not all([payment_status, authority, session_authority, reservation_data]) or authority != session_authority:
            return redirect("reservations:payment-fail")

        #  محاسبه مجدد قیمت
        try:
            room = get_object_or_404(Room, slug=reservation_data['room_slug'])
            check_in_jalali = jdatetime.date.fromisoformat(reservation_data['check_in'])
            check_out_jalali = jdatetime.date.fromisoformat(reservation_data['check_out'])
            nights = (check_out_jalali - check_in_jalali).days
            recalculated_price = nights * room.price
        except (ValueError, TypeError):
            return redirect("reservations:payment-fail")

        if recalculated_price != reservation_data['total_price']:
            return redirect("reservations:payment-fail")

        transaction_data = {
            'user': request.user,
            'amount': recalculated_price,
            'transaction_id': authority
        }

        if payment_status == "OK":
            data = {"merchant_id": settings.MERCHANT, "amount": recalculated_price * 10, "authority": authority}
            headers = {'content-type': 'application/json', 'Accept': 'application/json'}

            try:
                response = requests.post(ZP_API_VERIFY, data=json.dumps(data), headers=headers)
                response_data = response.json().get('data', {})

                if response_data.get('code') == 100:
                    try:
                        with transaction.atomic():
                            # تبدیل تاریخ شمسی یع میلادی قبل از ذخیره سازی
                            check_in_gregorian = check_in_jalali.togregorian()
                            check_out_gregorian = check_out_jalali.togregorian()

                            booking = Booking.objects.create(
                                user=request.user,
                                room=room,
                                check_in=check_in_gregorian,
                                check_out=check_out_gregorian,
                                people_count=reservation_data['capacity'],
                                status='confirmed',
                                total_price=recalculated_price,
                                nights_stay=reservation_data['nights']
                            )

                            guests_to_create = [Guest(booking=booking, **guest) for guest in reservation_data['guests']]
                            Guest.objects.bulk_create(guests_to_create)

                            transaction_data.update(status='success', booking=booking)
                            Transaction.objects.create(**transaction_data)

                    except Exception as e:
                        transaction_data['status'] = 'failed'
                        Transaction.objects.create(**transaction_data)
                        return redirect("reservations:payment-fail")

                    self.cleanup_session(request)
                    return redirect("reservations:payment-success", pk=booking.id)

                elif response_data.get('code') == 101:
                    self.cleanup_session(request)
                    return redirect("reservations:payment-success")


                else:
                    transaction_data['status'] = 'failed'
                    Transaction.objects.create(**transaction_data)
                    self.cleanup_session(request)
                    return redirect("reservations:payment-fail")

            except requests.RequestException:
                transaction_data['status'] = 'failed'
                Transaction.objects.create(**transaction_data)
                self.cleanup_session(request)
                return redirect("reservations:payment-fail")

        else:
            transaction_data['status'] = 'failed'
            Transaction.objects.create(**transaction_data)
            self.cleanup_session(request)
            return redirect("reservations:payment-fail")

    def cleanup_session(self, request):
        """ پاکسازی سشن پس از اتمام فرآیند پرداخت."""
        request.session.pop('reservation_data', None)
        request.session.pop('authority', None)
        request.session.modified = True


class PaymentSuccessView(LoginRequiredMixin, DetailView):
    model = Booking
    template_name = "reservations/payment_success.html"

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
