from django import forms
from hotels.models import Review, Booking
from django.core.validators import MinValueValidator, MaxValueValidator
from jalali_date.widgets import AdminJalaliDateWidget
import jdatetime


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


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out']
        widgets = {
            'check_in': AdminJalaliDateWidget(
                attrs={'class': 'form-control__room-detail booking-input'},
                format='%Y/%m/%d'
            ),
            'check_out': AdminJalaliDateWidget(
                attrs={'class': 'form-control__room-detail booking-input'},
                format='%Y/%m/%d'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today_jalali = jdatetime.date.today()
        self.fields['check_in'].initial = today_jalali.strftime('%Y/%m/%d')
        self.fields['check_out'].initial = today_jalali.strftime('%Y/%m/%d')
