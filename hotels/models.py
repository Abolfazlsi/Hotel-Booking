from django.db import models
from django.core.validators import MinValueValidator
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit


class Room(models.Model):
    title = models.CharField(max_length=100)
    price = models.IntegerField(validators=[MinValueValidator(0)])
    size = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    services = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

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
        options={'quality': 85},
    )
    alt_text = models.CharField(
        max_length=100,
        help_text='عکس اناق مورد نظر'
    )
    is_primary = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.room.title}"
