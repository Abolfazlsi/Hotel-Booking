from django.shortcuts import render, get_object_or_404, HttpResponse
from django.views.generic import TemplateView, ListView, DetailView, DeleteView, View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.template.defaultfilters import truncatewords
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from hotels.models import Room, Review, Service
from hotels.forms import ReviewForm, SearchForm, GuestForm
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
import jdatetime
from django.core.cache import cache
from reservations.models import Booking


def clear_cache(request):
    cache.clear()
    return HttpResponse("Clear")


class HomePage(TemplateView):
    template_name = "hotels/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rooms = Room.objects.filter(existing=True)[:5]
        rooms_list = [
            {
                'title': room.title,
                'price': room.price,
                'capacity': room.capacity,
                'description': room.description,
                'image_url': room.primary_image.image.url if room.primary_image else '',
                'alt_text': room.primary_image.alt_text if room.primary_image else '',
                'services': [service.name for service in room.services.all()],
                'url': room.get_absolute_url(),
                'rating': room.get_rating(),
            }
            for room in rooms
        ]
        context["rooms_list"] = rooms_list
        context["search_form"] = SearchForm(self.request.GET or None)
        return context


class RoomsListView(ListView):
    model = Room
    template_name = "hotels/rooms.html"
    paginate_by = 5
    context_object_name = 'room_list'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = Service.objects.all()
        context["search_form"] = SearchForm(self.request.GET or None)
        return context

    def get_queryset(self):
        queryset = Room.objects.all()

        check_in_str = self.request.GET.get('check_in')
        check_out_str = self.request.GET.get('check_out')
        people_count = self.request.GET.get('people')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if people_count and people_count.isdigit():
            queryset = queryset.filter(capacity=int(people_count))

        if min_price and min_price.isdigit():
            queryset = queryset.filter(price__gte=int(min_price))
        if max_price and max_price.isdigit():
            queryset = queryset.filter(price__lte=int(max_price))

        if check_in_str and check_out_str:
            try:
                check_in_j = jdatetime.date.fromisoformat(check_in_str.replace('/', '-'))
                check_out_j = jdatetime.date.fromisoformat(check_out_str.replace('/', '-'))
                check_in = check_in_j.togregorian()
                check_out = check_out_j.togregorian()

                overlapping_rooms = Booking.objects.filter(
                    status='confirmed',
                    check_in__lt=check_out,
                    check_out__gt=check_in
                ).values_list('room_id', flat=True).distinct()

                queryset = queryset.exclude(id__in=overlapping_rooms)
            except ValueError:
                pass
        return queryset

    def get(self, request, *args, **kwargs):
        rooms = self.get_queryset()
        sort = request.GET.get('sort', 'default')

        if sort == 'lower-price':
            rooms = rooms.order_by('price')
        elif sort == 'higher-price':
            rooms = rooms.order_by('-price')

        page = request.GET.get('page', 1)
        paginator = Paginator(rooms, self.paginate_by)
        try:
            room_list = paginator.page(page)
        except PageNotAnInteger:
            room_list = paginator.page(1)
        except EmptyPage:
            room_list = paginator.page(paginator.num_pages)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            room_data = []
            for room in room_list:
                room_data.append({
                    'title': room.title,
                    'price': room.price,
                    'capacity': room.capacity,
                    'size': room.size,
                    'description': truncatewords(room.description, 25),
                    'existing': 'exist' if room.existing else 'reserved',
                    'existing_text': 'موجود' if room.existing else 'رزرو شده',
                    'image_url': room.primary_image.image.url if room.primary_image else '',
                    'alt_text': room.primary_image.alt_text if room.primary_image else '',
                    'services': [service.name for service in room.services.all()],
                    'url': room.get_absolute_url(),
                })

            return JsonResponse({
                'room_list': room_data,
                'has_previous': room_list.has_previous(),
                'has_next': room_list.has_next(),
                'previous_page_number': room_list.previous_page_number() if room_list.has_previous() else None,
                'next_page_number': room_list.next_page_number() if room_list.has_next() else None,
                'current_page': room_list.number,
                'total_pages': paginator.num_pages,
                'total_rooms': paginator.count,
            })
        else:
            return render(request, self.template_name, {
                'room_list': room_list,
                'page_obj': room_list,
                'services': Service.objects.all(),
                'search_form': SearchForm(request.GET or None),
            })


@method_decorator(login_required, name='post')
class RoomDetailView(DetailView):
    model = Room
    template_name = "hotels/room_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ReviewForm()
        context['reviews'] = self.object.reviews.all()
        context['rating'] = self.object.get_rating()
        breakdown = self.object.get_rating_breakdown()
        context['rating_breakdown'] = [
            {'rating': i, 'percentage': breakdown[str(i)]}
            for i in range(5, 0, -1)
        ]


        check_in = self.request.GET.get('check_in')
        check_out = self.request.GET.get('check_out')
        today_jalali = jdatetime.date.today()
        errors = []


        if check_in:
            try:
                check_in = check_in.replace('-', '/')
                check_in_date = jdatetime.datetime.strptime(check_in, '%Y/%m/%d').date()
                if check_in_date < today_jalali:
                    errors.append("تاریخ ورود نمی‌تواند قبل از امروز باشد.")
                    check_in_date = today_jalali
            except ValueError:
                errors.append("فرمت تاریخ ورود نامعتبر است.")
                check_in_date = today_jalali
        else:
            check_in_date = today_jalali


        if check_out:
            try:
                check_out = check_out.replace('-', '/')
                check_out_date = jdatetime.datetime.strptime(check_out, '%Y/%m/%d').date()
                if check_out_date <= check_in_date:
                    errors.append("تاریخ خروج باید بعد از تاریخ ورود باشد.")
                    check_out_date = check_in_date + jdatetime.timedelta(days=1)
            except ValueError:
                errors.append("فرمت تاریخ خروج نامعتبر است.")
                check_out_date = check_in_date + jdatetime.timedelta(days=1)
        else:
            check_out_date = check_in_date + jdatetime.timedelta(days=1)


        nights = (check_out_date - check_in_date).days
        total_price = self.object.price * max(nights, 1)
        context['check_in'] = check_in_date
        context['check_out'] = check_out_date
        context['nights'] = max(nights, 1)
        context['total_price'] = total_price
        context['form_errors'] = errors

        context['guest_forms'] = [
            GuestForm(prefix=f'guest_{i}') for i in range(1, self.object.capacity + 1)
        ]

        return context

    def post(self, request, *args, **kwargs):
        room = self.get_object()
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.room = room
            review.user = request.user
            review.save()
            review_html = render_to_string('hotels/review_item.html', {
                'review': review,
                'request': request
            })
            breakdown = room.get_rating_breakdown()
            breakdown_list = [
                {'rating': i, 'percentage': breakdown[str(i)]}
                for i in range(5, 0, -1)
            ]
            return JsonResponse({
                'success': True,
                'review_html': review_html,
                'review_count': room.reviews.count(),
                'rating': room.get_rating(),
                'rating_breakdown': breakdown_list
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors.as_json()
            }, status=400)


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    http_method_names = ['delete']

    def get_success_url(self):
        return reverse('hotels:room_detail', kwargs={'slug': self.object.room.slug})

    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'لطفاً ابتدا وارد حساب کاربری خود شوید.'}, status=403)

        self.object = self.get_object()
        if self.object.user != request.user and not request.user.is_staff:
            return JsonResponse({'success': False, 'error': 'شما مجاز به حذف این کامنت نیستید.'}, status=403)

        room = self.object.room
        self.object.delete()

        # محاسبه اطلاعات به‌روز شده
        review_count = room.reviews.count()
        rating = room.get_rating()
        breakdown = room.get_rating_breakdown()
        breakdown_list = [
            {'rating': i, 'percentage': breakdown[str(i)]}
            for i in range(5, 0, -1)
        ]

        return JsonResponse({
            'success': True,
            'review_count': review_count,
            'rating': rating,
            'rating_breakdown': breakdown_list
        }, status=200)


class ReviewEditView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            review = get_object_or_404(Review, pk=kwargs['pk'])
            # بررسی مالکیت نظر
            if review.user != request.user and not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': 'شما اجازه ویرایش این نظر را ندارید.'
                }, status=403)
            return JsonResponse({
                'success': True,
                'review': {
                    'rating': review.rating,
                    'comment': review.comment
                }
            })
        except Review.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'نظر مورد نظر یافت نشد.'
            }, status=404)

    def post(self, request, *args, **kwargs):
        try:
            review = get_object_or_404(Review, pk=kwargs['pk'])
            # بررسی مالکیت نظر
            if review.user != request.user and not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': 'شما اجازه ویرایش این نظر را ندارید.'
                }, status=403)
            form = ReviewForm(request.POST, instance=review)
            if form.is_valid():
                review = form.save()
                # رندر HTML نظر به‌روزرسانی‌شده برای پاسخ AJAX
                review_html = render_to_string('hotels/review_item.html', {
                    'review': review,
                    'request': request
                })
                # آماده‌سازی rating_breakdown برای AJAX
                breakdown = review.room.get_rating_breakdown()
                breakdown_list = [
                    {'rating': i, 'percentage': breakdown[str(i)]}
                    for i in range(5, 0, -1)
                ]
                return JsonResponse({
                    'success': True,
                    'review_html': review_html,
                    'review_count': review.room.reviews.count(),
                    'rating': review.room.get_rating(),
                    'rating_breakdown': breakdown_list
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
        except Review.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'نظر مورد نظر یافت نشد.'
            }, status=404)


class RoomSearchView(ListView):
    model = Room
    template_name = "hotels/rooms.html"

    def get_queryset(self):
        pass
