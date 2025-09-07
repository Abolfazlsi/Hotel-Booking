from django.urls import path, re_path
from reservations import views
from django.views.generic import TemplateView

app_name = 'reservations'

urlpatterns = [
    # payment
    re_path(r"send-request/(?P<slug>[-\w]+)/", views.SendRequestView.as_view(), name="send-request"),
    path("payment-verify/", views.VerifyView.as_view(), name="payment-verify"),

    # payment status
    path("payment-success/<int:pk>/", views.PaymentSuccessView.as_view(), name="payment-success"),
    path("payment-failed/", TemplateView.as_view(template_name='reservations/payment_fail.html'), name="payment-fail"),

]
