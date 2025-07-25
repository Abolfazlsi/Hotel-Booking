from django import forms
from hotels.models import Review
from django.core.validators import MinValueValidator, MaxValueValidator


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
