# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User
from django.core.exceptions import ValidationError
from django.core import validators
from django.core.validators import RegexValidator


class UserCreationForm(UserCreationForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['phone', 'first_name', "last_name", 'email', 'is_admin', 'is_superuser', 'groups', 'user_permissions']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # ذخیره گروه‌ها و مجوزها
            if self.cleaned_data.get('groups'):
                user.groups.set(self.cleaned_data['groups'])
            if self.cleaned_data.get('user_permissions'):
                user.user_permissions.set(self.cleaned_data['user_permissions'])
        return user


class UserChangeForm(BaseUserChangeForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ['phone', 'first_name', "last_name", 'email', 'is_active', 'is_admin', 'groups', 'user_permissions']


class SignInSignUpForm(forms.Form):
    phone = forms.CharField(max_length=11, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "شماره تلفن خود را وارد کنید"}),
                            validators=[RegexValidator(r'^09\d{9}$', 'شماره تلفن باید با 09 شروع شود و 11 رقم باشد.')])
    email = forms.EmailField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ادرس ایمیل"}))


class OtpVerifyForm(forms.Form):
    code = forms.CharField(max_length=4, min_length=4,
                           widget=forms.TextInput(attrs={"class": "form-control",
                                                         "placeholder": "کد تایید ارسال شده به شماره موبایل را وارد کنید"}))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone', 'first_name', 'last_name', 'email']

        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
