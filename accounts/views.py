from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from accounts.forms import SignInSignUpForm, OtpVerifyForm, UserProfileForm
from accounts.models import User
from hotels.models import Room
import secrets
import redis
from django.conf import settings
from decouple import config
from accounts.send_otp import send_otp
from django.contrib.auth import login, logout

redis_client = redis.Redis.from_url(config('REDIS_URL', default='redis://localhost:6379/0'))


class SignInSignUpView(View):
    def get(self, request):
        form = SignInSignUpForm()
        return render(request, "accounts/singIn_singUp.html", {"form": form})

    def post(self, request):
        form = SignInSignUpForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            try:
                code = secrets.randbelow(9000) + 1000
                token = secrets.token_urlsafe(11)

                otp_key = f"otp:{phone}:{token}"

                redis_client.setex(otp_key, 120, code)

                request.session["otp_token"] = token
                request.session["otp_phone"] = phone

                send_otp(code, phone)
                messages.success(request, "کد تایید ارسال شد")
            except:
                messages.error(request, "مشکلی در اتصال پیش امده است")

            return redirect("accounts:verify_otp")
        else:
            messages.error(request, "شمره تلفن نامعتبر است")

        return render(request, "accounts/singIn_singUp.html", {"form": form})


class OtpVerifyView(View):
    def get(self, request):
        if not request.session.get("otp_token"):
            return redirect("accounts:signin-signup")
        form = OtpVerifyForm()
        return render(request, "accounts/otp_verify.html", {"form": form})

    def post(self, request):
        form = OtpVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            otp_token = request.session.get("otp_token")
            otp_phone = request.session.get("otp_phone")

            if not otp_token or not otp_phone:
                messages.error(request, "مشکلی پیش امده است")
                return redirect("accounts:signin-signup")

            otp_key = f"otp:{otp_phone}:{otp_token}"
            try:
                get_verify_code = redis_client.get(otp_key)
                if get_verify_code and get_verify_code.decode("utf-8") == str(code):
                    user, create = User.objects.get_or_create(phone=otp_phone)
                    if create:
                        user.set_unusable_password()
                        user.save()

                    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                    redis_client.delete(otp_key)

                    messages.success(request, "ثبت نام با موفقیت انجام شد")
                    return redirect("hotels:home")
                else:
                    messages.error(request, "کد تایید نامعتبر است")
            except:
                messages.error(request, "مشکلی در اتصال پیش امده است")


        else:
            messages.error(request, "کد تایید نامعتبر است")

        return render(request, "accounts/otp_verify.html", {"form": form})


def log_out(request):
    user = request.user
    if user.is_authenticated:
        logout(request)
        messages.error(request, "شما از حساب کاربری خود خارج شدید")
        return redirect("hotels:home")


class UserProfileView(View):
    def get(self, request):
        user = request.user
        form = UserProfileForm(instance=user)
        return render(request, "accounts/profile.html", {"form": form})

    def post(self, request):
        user = request.user
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات حساب کاربری تغییر یافت.")
            return redirect("accounts:user_profile")
        return render(request, "accounts/profile.html", {"form": form})
