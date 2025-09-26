from django.test import TestCase
from accounts.models import User
from django.core.exceptions import ValidationError


class UserManagerTests(TestCase):

    def test_create_user_success(self):
        user = User.objects.create_user(phone="09121234567", password="testpass123")
        self.assertEqual(user.phone, "09121234567")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff) if hasattr(user, "is_staff") else None

    def test_create_user_without_phone_raises_error(self):
        with self.assertRaisesMessage(ValueError, "Users must have a phone number"):
            User.objects.create_user(phone=None, password="testpass123")

    def test_create_user_without_password_raises_error(self):
        with self.assertRaisesMessage(ValueError, "Password is required"):
            User.objects.create_user(phone="09120000000", password=None)

    def test_create_superuser_success(self):
        admin = User.objects.create_superuser(phone="09121111111", password="adminpass123")
        self.assertEqual(admin.phone, "09121111111")
        self.assertTrue(admin.check_password("adminpass123"))
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_admin)


class UserModelTests(TestCase):

    def test_create_user_with_valid_phone(self):
        user = User.objects.create_user(phone="09121234567", password="strongpass")
        self.assertEqual(user.phone, "09121234567")
        self.assertTrue(user.check_password("strongpass"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(phone="09121111111", password="adminpass")
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_phone_validator_invalid_number(self):
        user = User(phone="12345", password="test123")
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_str_method_with_first_name(self):
        user = User.objects.create(
            phone="09120000000",
            password="testpass",
            first_name="abol",
            last_name="احمدی"
        )
        self.assertEqual(str(user), "abol (09120000000)")

    def test_str_method_without_first_name(self):
        user = User.objects.create_user(
            phone="09123334444",
            password="testpass"
        )
        self.assertEqual(str(user), "کاربر با شماره تلفن (09123334444)")

    def test_is_staff_returns_is_admin(self):
        user = User.objects.create_user(phone="09121112222", password="pass123")
        self.assertFalse(user.is_staff)
        user.is_admin = True
        self.assertTrue(user.is_staff)
