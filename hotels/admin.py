from django.contrib import admin
from hotels.models import RoomImage, Room, Service, Review
import jdatetime


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'size', "existing", 'capacity', 'created_at_jalali']
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    inlines = [RoomImageInline]
    fieldsets = [
        ("اطلاعات", {'fields': ['title', 'price', 'size', 'capacity', "existing"]}),
        ('جزئیات', {'fields': ['services', 'description']}),

    ]

    def created_at_jalali(self, obj):
        if obj.created_at:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return jalali_date.strftime('%Y/%m/%d %H:%M:%S')
        return ''

    created_at_jalali.short_description = 'تاریخ ایجاد'


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
    list_display = ["room", "user", "rating", "is_featured", "created_at_jalali"]
    list_filter = ["rating", "room"]
    search_fields = ["user", "room"]
    list_editable = ["is_featured"]

    def created_at_jalali(self, obj):
        if obj.created_at:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return jalali_date.strftime('%Y/%m/%d %H:%M:%S')
        return ''

    created_at_jalali.short_description = 'تاریخ ایجاد'
