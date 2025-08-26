from django.db import models
from django.core.validators import MinValueValidator
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
from django.utils.text import slugify
from django.urls import reverse
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import jdatetime
import django_jalali.db.models as jmodels


class Service(models.Model):
    name = models.CharField(max_length=20, verbose_name="نام")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "سرویس"
        verbose_name_plural = "سرویس ها"


class Room(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان")
    price = models.IntegerField(validators=[MinValueValidator(0)], verbose_name="قیمت")
    size = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="اندازه اتاق(به متر)")
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="ظرفیت تعداد نفرات اتاق")
    services = models.ManyToManyField(Service, related_name="rooms", verbose_name="سرویس ها اتاق")
    description = models.TextField(verbose_name="توضیحات")
    slug = models.SlugField(unique=True, null=True, blank=True, allow_unicode=True)
    existing = models.BooleanField(default=True, verbose_name="موجود بودن اتاق")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "اتاق"
        verbose_name_plural = "اتاق ها"

    def save(self, *args, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.title, allow_unicode=True)
        super(Room, self).save()

    def get_absolute_url(self):
        return reverse("hotels:room_detail", args=[self.slug])

    def get_rating(self):
        from django.db.models import Avg
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0.0

    def get_rating_breakdown(self):
        from django.db.models import Count
        total_reviews = self.reviews.count()
        if total_reviews == 0:
            return {str(i): 0 for i in range(1, 6)}
        breakdown = self.reviews.values('rating').annotate(count=Count('rating')).order_by('-rating')
        percentages = {str(i): 0 for i in range(1, 6)}
        for item in breakdown:
            percentages[str(item['rating'])] = (item['count'] / total_reviews) * 100
        return percentages

    def __str__(self):
        return self.title

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()

    def created_at_jalali(self):
        jalali_date = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jalali_date.strftime('%Y/%m/%d %H:%M:%S')


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images", verbose_name="اتاق")
    image = ProcessedImageField(
        upload_to='rooms/images',
        processors=[ResizeToFit(800, 600)],
        verbose_name="عکس"
    )
    alt_text = models.CharField(
        max_length=100,
        verbose_name="توضیح عکس"
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="عکس اصلی اتاق"
    )

    def __str__(self):
        return f"{self.room.title}"

    class Meta:
        verbose_name = "عکس اتاق"
        verbose_name_plural = "عکس اتاق ها"


class Review(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reviews", verbose_name="اتاق")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews", verbose_name="کاربر")
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="امتیاز")
    comment = models.TextField(verbose_name="متن نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد شدن")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"

    def __str__(self):
        return f" {self.user.first_name} {self.user.last_name} --> {self.room}"

    def time_since_creation(self):
        time_delta = timezone.now() - self.created_at
        days = time_delta.days
        hours, remainder = divmod(time_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days >= 365:
            years = days // 365
            return f"{years} سال پیش"
        elif days >= 30:
            months = days // 30
            return f"{months} ماه پیش"
        elif days > 0:
            return f"{days} روز پیش"
        elif hours > 0:
            return f"{hours} ساعت پیش"
        elif minutes > 0:
            return f"{minutes} دقیقه پیش"
        else:
            return f"{seconds} ثانیه پیش"

    def created_at_jalali(self):
        # تبدیل تاریخ میلادی به شمسی
        jalali_date = jdatetime.datetime.fromgregorian(datetime=self.created_at)
        return jalali_date.strftime('%Y/%m/%d %H:%M:%S')

