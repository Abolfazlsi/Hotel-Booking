from django.db import models
from django.core.validators import MinValueValidator
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
from django.utils.text import slugify
from django.urls import reverse
from accounts.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Service(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Room(models.Model):
    title = models.CharField(max_length=100)
    price = models.IntegerField(validators=[MinValueValidator(0)])
    size = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    services = models.ManyToManyField(Service, related_name="rooms")
    description = models.TextField()
    slug = models.SlugField(unique=True, null=True, blank=True, allow_unicode=True)
    existing = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

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


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="images")
    image = ProcessedImageField(
        upload_to='rooms/images',
        processors=[ResizeToFit(800, 600)],
    )
    alt_text = models.CharField(
        max_length=100,
    )
    is_primary = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.room.title}"


class Review(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.room} - {self.user.first_name} {self.user.last_name}"

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
