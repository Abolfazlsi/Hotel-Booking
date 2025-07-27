from django.urls import path
from accounts import views

app_name = "accounts"

urlpatterns = [
    # sign up
    path("singin-singup/", views.SignInSignUpView.as_view(), name="signin-signup"),
    path("otp-verify/", views.OtpVerifyView.as_view(), name="verify_otp"),

    # logout
    path("logout/", views.log_out, name="logout"),

    # user profile
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),

]
