from django.urls import path, re_path
from reservations import views

app_name = 'reservations'

urlpatterns = [
    re_path(r"send-request/(?P<slug>[-\w]+)/", views.SendRequestView.as_view(), name="send-request"),
    path("payment-verify/", views.VerifyView.as_view(), name="payment-verify"),
]
