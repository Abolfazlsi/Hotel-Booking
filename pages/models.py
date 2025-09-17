from django.db import models
from django.core.validators import RegexValidator
from accounts.models import User


class ContactUs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contact_us", null=True)
    full_name = models.CharField(max_length=100, verbose_name="نام کامل")
    phone = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^09\d{9}$', 'شماره تلفن باید با 09 شروع شود و 11 رقم باشد.')],
        verbose_name="شماره موبایل"
    )
    email = models.EmailField(max_length=255, verbose_name="ادرس ایمیل")
    subject = models.CharField(max_length=255, verbose_name="موضوع")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.subject}"

    class Meta:
        verbose_name = "تماس با ما"
        verbose_name_plural = "تماس با ما"
