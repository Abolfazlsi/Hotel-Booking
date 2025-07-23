from django.db import models
from django.core.validators import MinValueValidator
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit
from django.utils.text import slugify
from django.urls import reverse


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, force_insert=False, force_update=False, using=None, update_fields=None):
        self.slug = slugify(self.title, allow_unicode=True)
        super(Room, self).save()

    def get_absolute_url(self):
        return reverse("hotels:room_detail", args=[self.slug])

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
