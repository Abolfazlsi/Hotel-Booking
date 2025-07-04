from django.urls import path
from accounts import views

app_name = "accounts"

urlpatterns = [
    # accounts
    path("singin-singup/", views.SignInSignUpView.as_view(), name="signin-signup"),
    path("otp-verify/", views.OtpVerifyView.as_view(), name="verify_otp"),

]
