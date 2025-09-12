from django import forms
from hotels.models import Review
from reservations.models import Booking, Guest
from django.forms import inlineformset_factory
from django.core.validators import MinValueValidator, MaxValueValidator
from jalali_date.widgets import AdminJalaliDateWidget
from jalali_date.fields import JalaliDateField
from jdatetime import date as jdate, timedelta


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'required': 'required',
                'placeholder': 'نظر خود را اینجا بنویسید...',
            }),
            'rating': forms.HiddenInput(attrs={'id': 'rating-value'}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError('امتیاز باید بین ۱ تا ۵ باشد.')
        return rating


class SearchForm(forms.Form):
    check_in = JalaliDateField(
        widget=AdminJalaliDateWidget(
            attrs={
                'class': 'form-control__room-detail booking-input',
                'id': 'check_in',
                'placeholder': 'تاریخ ورود'
            },
            format='%Y/%m/%d'
        ),
        label='تاریخ ورود'
    )
    check_out = JalaliDateField(
        widget=AdminJalaliDateWidget(
            attrs={
                'class': 'form-control__room-detail booking-input',
                'id': 'check_out',
                'placeholder': 'تاریخ خروج'
            },
            format='%Y/%m/%d'
        ),
        label='تاریخ خروج'
    )
    people_count = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'id': 'people_count'}),
        label='تعداد نفرات',
        initial=2
    )
    min_price = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'id': 'min_price'}),
        required=False,
        label='حداقل قیمت'
    )
    max_price = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'id': 'max_price'}),
        required=False,
        label='حداکثر قیمت'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today_jalali = jdate.today()
        self.fields['check_in'].initial = today_jalali.strftime('%Y/%m/%d')
        self.fields['check_out'].initial = (today_jalali + timedelta(days=2)).strftime('%Y/%m/%d')

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        # تبدیل تاریخ‌های با خط تیره به اسلش
        if isinstance(check_in, str):
            cleaned_data['check_in'] = check_in.replace('-', '/')
        if isinstance(check_out, str):
            cleaned_data['check_out'] = check_out.replace('-', '/')

        # اعتبارسنجی: تاریخ خروج باید بعد از تاریخ ورود باشه
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError("تاریخ خروج باید بعد از تاریخ ورود باشد.")

        return cleaned_data


class GuestForm(forms.ModelForm):
    """فرم برای ثبت اطلاعات یک مهمان بر اساس مدل Guest"""

    class Meta:
        model = Guest
        fields = ['full_name', 'national_id', 'phone_number', 'gender']
        widgets = {
            'full_name': forms.TextInput(attrs={'required': True, 'class': 'form-control__room-detail booking-input'}),
            'national_id': forms.TextInput(
                attrs={'maxlength': 10, 'required': True, 'class': 'form-control__room-detail booking-input'}),
            'phone_number': forms.TextInput(
                attrs={'maxlength': 11, 'required': True, 'class': 'form-control__room-detail booking-input'}),
            'gender': forms.Select(attrs={'required': True, 'class': 'form-control__room-detail booking-input'}),
        }
        labels = {
            'full_name': 'نام کامل',
            'national_id': 'کد ملی',
            'phone_number': 'شماره تلفن',
            'gender': 'جنسیت',
        }
