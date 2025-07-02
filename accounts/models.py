from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from django.core.validators import RegexValidator
import uuid


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None):
        if not phone:
            raise ValueError("Users must have a phone number")
        if not password:
            raise ValueError("Password is required")

        user = self.model(phone=phone)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None):
        user = self.create_user(phone, password=password)
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, null=True, blank=True, unique=True)
    fullname = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(
        max_length=11,
        unique=True,
        validators=[RegexValidator(r'^09\d{9}$', 'شماره تلفن باید با 09 شروع شود و 11 رقم باشد.')]
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'

    def __str__(self):
        return f"{self.fullname or 'User'} ({self.phone})"

    @property
    def is_staff(self):
        return self.is_admin


