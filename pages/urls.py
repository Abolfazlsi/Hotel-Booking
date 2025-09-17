from django.urls import path
from pages import views

app_name = 'pages'
urlpatterns = [
    path("contact-us/", views.ContactUsView.as_view(), name="contact_us"),
]
