from django.contrib import admin
from hotels.models import RoomImage, Room, Service, Review


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'size', "existing", 'capacity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    inlines = [RoomImageInline]
    fieldsets = [
        (None, {'fields': ['title', 'price', 'size', 'capacity', "existing"]}),
        ('جزئیات', {'fields': ['services', 'description']}),
        ('اسلاگ', {'fields': ['slug']}),

    ]


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ['room', 'alt_text', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['room__title', 'alt_text']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["name"]
    search_fields = ["name"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["room", "user", "rating", "created_at"]
    list_filter = ["rating", "room"]
    search_fields = ["user", "room"]
    exclude = ["created_at"]
