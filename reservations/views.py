from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.conf import settings
from django.views.generic import View
from hotels.models import Room
import json
import requests

if settings.SANDBOX:
    sandbox = 'sandbox'
else:
    sandbox = 'payment'

ZP_API_REQUEST = f"https://{sandbox}.zarinpal.com/pg/v4/payment/request.json"
ZP_API_STARTPAY = f"https://{sandbox}.zarinpal.com/pg/StartPay/"
ZP_API_VERIFY = f"https://{sandbox}.zarinpal.com/pg/v4/payment/verify.json"

description = "Hello my dear friend"

CallbackURL = 'http://127.0.0.1:8000/cart/verify/'


# payment gateway
class SendRequestAPIView(View):

    def post(self, request, slug):
        room = get_object_or_404(Room, slug=slug)

        data = {
            "merchant_id": settings.MERCHANT,
            "amount": room.price,
            "description": description,
            "callback_url": CallbackURL,
        }
        data = json.dumps(data)

        headers = {'content-type': 'application/json', 'content-length': str(len(data))}

        response = requests.post(ZP_API_REQUEST, data=data, headers=headers)

        if response.status_code == 200:
            response = response.json()

            if response["data"]['code'] == 100:
                url = f"{ZP_API_STARTPAY}{response['data']['authority']}"
                return redirect(url)
            else:
                return HttpResponse(str(response["error"]))
        else:
            return HttpResponse("مشکلی پیش امده است")


# verify payment gateway
class VerifyAPIView(APIView):

    def get(self, request):
        payment_status = request.query_params.get('Status')
        authority = request.query_params.get('Authority')

        order_id = request.session.get('order_id')
        if not order_id:
            return Response({"error": "order bot found"})

        order = get_object_or_404(Order, id=int(order_id))

        if payment_status == "OK":
            data = {
                "merchant_id": settings.MERCHANT,
                "amount": order.total,
                "authority": authority
            }
            data = json.dumps(data)

            headers = {'content-type': 'application/json', 'Accept': 'application/json'}

            response = requests.post(ZP_API_VERIFY, data=data, headers=headers)

            if response.status_code == 200:
                response_data = response.json()

                if response_data['data']['code'] == 100:
                    order.is_paid = True
                    order.save()
                    return Response({"message": "payment was successfully", "order_id": order.id})

                elif response_data['data']['code'] == 101:
                    return Response({"message": "payment has already been made"}, status=status.HTTP_200_OK)

                else:
                    return Response({"error": "payment failed"}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({"error": "error connecting to the payment gateway"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({"error": "payment canceled by user"}, status=status.HTTP_200_OK)
