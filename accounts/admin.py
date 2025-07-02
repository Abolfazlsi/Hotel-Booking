# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserChangeForm, UserCreationForm
from .models import User


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ["phone", "fullname", "is_admin", "is_active"]
    list_filter = ["is_admin", "is_active"]
    fieldsets = [
        (None, {"fields": ["phone", "password"]}),
        ("Personal Info", {"fields": ["fullname", "email"]}),
        ("Permissions", {"fields": ["is_admin", "is_active", "is_superuser", "groups", "user_permissions"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ["phone", "password1", "password2", "fullname", "email", "groups", "user_permissions"],
            },
        ),
    ]
    search_fields = ["phone", "fullname"]
    ordering = ["phone"]
    filter_horizontal = ["groups", "user_permissions"]

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     is_superuser = request.user.is_superuser
    #     if not is_superuser:
    #         form.base_fields["is_admin"].disabled = True
    #         form.base_fields["groups"].disabled = True
    #         form.base_fields["user_permissions"].disabled = True
    #     return form


admin.site.register(User, UserAdmin)
