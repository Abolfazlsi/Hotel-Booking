from django import forms
from pages.models import ContactUs


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = "__all__"
        exclude = ["user"]

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "id": "fullName"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "id": "phone"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "id": "email"}),
            "subject": forms.TextInput(attrs={"class": "form-control", "id": "subject"}),
            "message": forms.Textarea(attrs={"class": "form-control", "id": "message", "rows": 5}),
        }
