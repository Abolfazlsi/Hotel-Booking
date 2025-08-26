from django.contrib import admin
from reservations.models import Booking, Guest, Transaction
import jdatetime
from django.db import models
from jalali_date.widgets import AdminJalaliDateWidget
from reservations.widgets import CustomJalaliDateWidget
from django.contrib.humanize.templatetags.humanize import intcomma


def format_price(value):
    """فرمت کردن عدد با جداکننده سه‌رقمی (مثل 1,000,000)"""
    try:
        return "{:,.0f}".format(value)
    except (ValueError, TypeError):
        return value


class GuestStackedInline(admin.TabularInline):
    model = Guest


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'room',
        'people_count',
        'get_check_in_jalali',
        'get_check_out_jalali',
        'status',
        'get_total_price_formatted',
        'created_at_jalali',
    )
    inlines = (GuestStackedInline,)
    list_filter = (
        'status',
        'room',
        'check_in',
        'check_out',
    )
    search_fields = (
        'user__first_name',
        'user__last_name',
        'room__title',
    )
    list_editable = ('status',)
    list_per_page = 25
    ordering = ('-created_at',)
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    autocomplete_fields = ('user', 'room')

    # تنظیم ویجت تقویم شمسی برای فیلدهای DateField
    formfield_overrides = {
        models.DateField: {'widget': CustomJalaliDateWidget},
    }

    @admin.display(description='تاریخ ورود', ordering='check_in')
    def get_check_in_jalali(self, obj):
        if obj.check_in:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.check_in)
            return jalali_date.strftime('%Y/%m/%d')
        return ''

    @admin.display(description='تاریخ خروج', ordering='check_out')
    def get_check_out_jalali(self, obj):
        if obj.check_out:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.check_out)
            return jalali_date.strftime('%Y/%m/%d')
        return ''

    @admin.display(description='تاریخ ایجاد (شمسی)', ordering='created_at')
    def created_at_jalali(self, obj):
        if obj.created_at:
            try:
                jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
                return jalali_date.strftime('%Y/%m/%d %H:%M:%S')
            except (ValueError, TypeError):
                return ''
        return ''

    @admin.display(description='قیمت کل (تومان)', ordering='total_price')
    def get_total_price_formatted(self, obj):
        return f"{format_price(obj.total_price)} تومان"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'room')


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = (
        'booking',
        'full_name',
        'national_id',
        'phone_number',
        'gender',
    )
    list_filter = ('gender', 'booking')
    search_fields = (
        'full_name',
        'national_id',
        'phone_number',
    )
    list_per_page = 25
    ordering = ('-id',)
    autocomplete_fields = ('booking',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('booking')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id',
        'user',
        'booking',
        'get_amount_formatted',
        'status',
        'created_at_jalali',
    )
    list_filter = (
        'status',
        'created_at',
    )
    search_fields = (
        'transaction_id',
        'user__first_name',
        'user__last_name',
        'user__username',
        'booking__id',
    )
    list_per_page = 25
    ordering = ('-created_at',)
    autocomplete_fields = ('user', 'booking')
    readonly_fields = ('transaction_id', 'amount', 'created_at')

    @admin.display(description='مبلغ (تومان)', ordering='amount')
    def get_amount_formatted(self, obj):
        return f"{format_price(obj.amount)} تومان"

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_jalali(self, obj):
        if obj.created_at:
            try:
                jalali_date = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
                return jalali_date.strftime('%Y/%m/%d %H:%M:%S')
            except (ValueError, TypeError):
                return ''
        return ''

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'booking')
