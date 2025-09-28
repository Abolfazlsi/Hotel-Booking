from django.db import models
from accounts.models import User
from hotels.models import Room
from django.core.validators import MinValueValidator, RegexValidator
import jdatetime
from datetime import date
from django.db import transaction


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار تایید'),
        ('confirmed', 'تأیید شده'),
        ('canceled', 'لغو شده'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="کاربر"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="اتاق"
    )
    check_in = models.DateField(verbose_name="تاریخ ورود", null=True)
    check_out = models.DateField(verbose_name="تاریخ خروج", null=True)
    people_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="تعداد نفرات"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت رزرو"
    )
    total_price = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="قیمت کل",
        null=True
    )
    nights_stay = models.PositiveIntegerField(validators=[MinValueValidator(1)], null=True, verbose_name="تعداد شب اقامت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")

    class Meta:
        verbose_name = "رزرو"
        verbose_name_plural = "رزروها"
        ordering = ['-created_at']

    def __str__(self):
        user_name = f"{self.user.first_name} {self.user.last_name}".strip() if (self.user.first_name and
                                                                                self.user.last_name is not "") else self.user.phone
        return f"رزرو {self.room.title} توسط {user_name} "

    def nights(self):
        if isinstance(self.check_in, date) and isinstance(self.check_out, date):
            try:
                return (self.check_out - self.check_in).days
            except (ValueError, TypeError):
                return 0
        return 0

    def clean(self):
        from django.core.exceptions import ValidationError
        if isinstance(self.check_in, date) and isinstance(self.check_out, date):
            if self.check_out <= self.check_in:
                raise ValidationError("تاریخ خروج باید بعد از تاریخ ورود باشد.")
        if self.people_count > self.room.capacity:
            raise ValidationError(f"تعداد نفرات نمی‌تواند بیشتر از ظرفیت اتاق ({self.room.capacity}) باشد.")
        if isinstance(self.check_in, date) and isinstance(self.check_out, date):
            conflicting_bookings = Booking.objects.filter(
                room=self.room,
                status__in=['pending', 'confirmed'],
                check_in__lte=self.check_out,
                check_out__gte=self.check_in
            ).exclude(id=self.id)
            if conflicting_bookings.exists():
                raise ValidationError("اتاق در تاریخ‌های انتخاب‌شده در دسترس نیست.")

    def save(self, *args, **kwargs):
        if self.room and isinstance(self.check_in, date) and isinstance(self.check_out, date):
            nights = self.nights()
            self.total_price = self.room.price * nights

        is_new = self._state.adding

        with transaction.atomic():
            super().save(*args, **kwargs)

            if self.status == 'confirmed':
                room_to_update = Room.objects.select_for_update().get(pk=self.room.pk)
                if room_to_update.existing:
                    room_to_update.existing = False
                    room_to_update.save(update_fields=['existing'])

            elif self.status == 'canceled' and not is_new:
                if not Booking.objects.filter(
                        room=self.room,
                        status='confirmed',
                        check_out__gt=self.check_in
                ).exclude(pk=self.pk).exists():
                    room_to_update = Room.objects.select_for_update().get(pk=self.room.pk)
                    if not room_to_update.existing:
                        room_to_update.existing = True
                        room_to_update.save(update_fields=['existing'])


class Guest(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='guests', verbose_name="رزرو")
    full_name = models.CharField(max_length=150, verbose_name="نام کامل")
    national_id = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{10}$', 'کد ملی باید ۱۰ رقم باشد.')],
                                   verbose_name="کد ملی")
    phone_number = models.CharField(max_length=11, validators=[
        RegexValidator(r'^09\d{9}$', 'شماره تلفن باید با ۰۹ شروع شده و ۱۱ رقم باشد.')], verbose_name="شماره تلفن")
    gender = models.CharField(max_length=10, choices=[("M", "مرد"), ("F", "زن")], verbose_name="جنسیت")

    class Meta:
        verbose_name = "مهمان"
        verbose_name_plural = "مهمان ها"

    def __str__(self):
        return f"{self.full_name} --> {self.booking}"


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="کاربر"
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='transaction',
        verbose_name="رزرو",
        null=True,
        blank=True
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="مبلغ"
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="شناسه تراکنش"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='failed',
        verbose_name="وضعیت تراکنش"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"

    def __str__(self):
        return f"تراکنش {self.transaction_id} برای {self.booking if self.booking else 'بدون رزرو'}"
