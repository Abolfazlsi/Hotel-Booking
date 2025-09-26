from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.forms import UserCreationForm, UserChangeForm, SignInSignUpForm
from accounts.models import User


class UserCreationFormTest(TestCase):

    def setUp(self):
        self.test_group = Group.objects.create(name='Test Group')
        content_type = ContentType.objects.get_for_model(User)
        self.test_permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type,
        )

        self.valid_data = {
            'phone': '09123456789',
            'first_name': 'علی',
            'last_name': 'احمدی',
            'email': 'ali@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'is_admin': False,
            'is_superuser': False,
            'groups': [self.test_group.id],
            'user_permissions': [self.test_permission.id],
        }

    def test_form_with_valid_data(self):
        form = UserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_form_save_creates_user(self):
        form = UserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertIsInstance(user, User)
        self.assertEqual(user.phone, '09123456789')
        self.assertEqual(user.first_name, 'علی')
        self.assertEqual(user.last_name, 'احمدی')
        self.assertEqual(user.email, 'ali@example.com')

        self.assertTrue(user.check_password('testpass123'))

        self.assertIn(self.test_group, user.groups.all())
        self.assertIn(self.test_permission, user.user_permissions.all())

    def test_form_without_phone(self):
        data = self.valid_data.copy()
        del data['phone']
        form = UserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_form_with_invalid_phone(self):
        invalid_phones = [
            '0912345678',
            '091234567890',
            '08123456789',
            '9123456789',
            'abcdefghijk',
        ]

        for invalid_phone in invalid_phones:
            data = self.valid_data.copy()
            data['phone'] = invalid_phone
            form = UserCreationForm(data=data)
            self.assertFalse(form.is_valid(), f"Phone {invalid_phone} should be invalid")
            self.assertIn('phone', form.errors)

    def test_form_with_duplicate_phone(self):
        User.objects.create_user(phone='09123456789', password='pass123')

        form = UserCreationForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_form_password_mismatch(self):
        data = self.valid_data.copy()
        data['password2'] = 'differentpass123'
        form = UserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertEqual(form.errors['password2'][0], "Passwords don't match")

    def test_form_without_password(self):
        data = self.valid_data.copy()
        del data['password1']
        del data['password2']
        form = UserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password1', form.errors)
        self.assertIn('password2', form.errors)

    def test_form_with_invalid_email(self):
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        form = UserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_form_optional_fields(self):
        data = {
            'phone': '09123456789',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = UserCreationForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertIsNone(user.first_name)
        self.assertIsNone(user.last_name)
        self.assertIsNone(user.email)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_superuser)

    def test_form_with_admin_privileges(self):
        data = self.valid_data.copy()
        data['is_admin'] = True
        data['is_superuser'] = True

        form = UserCreationForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertTrue(user.is_admin)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)  # باید True باشد چون is_admin = True


class UserChangeFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            phone='09123456789',
            first_name='علی',
            last_name='احمدی',
            email='ali@example.com',
            password='oldpass123'
        )

        self.test_group = Group.objects.create(name='Test Group')
        content_type = ContentType.objects.get_for_model(User)
        self.test_permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type,
        )

        self.valid_data = {
            'phone': '09123456789',
            'first_name': 'علی',
            'last_name': 'احمدی جدید',
            'email': 'ali_new@example.com',
            'is_active': True,
            'is_admin': False,
            'groups': [self.test_group.id],
            'user_permissions': [self.test_permission.id],
        }

    def test_form_with_valid_data(self):
        form = UserChangeForm(instance=self.user, data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_form_save_updates_user(self):
        form = UserChangeForm(instance=self.user, data=self.valid_data)
        self.assertTrue(form.is_valid())
        updated_user = form.save()

        self.assertEqual(updated_user.last_name, 'احمدی جدید')
        self.assertEqual(updated_user.email, 'ali_new@example.com')

        self.assertIn(self.test_group, updated_user.groups.all())
        self.assertIn(self.test_permission, updated_user.user_permissions.all())

    def test_form_password_field_is_readonly(self):
        form = UserChangeForm(instance=self.user)
        self.assertIn('password', form.fields)
        self.assertTrue(hasattr(form.fields['password'], 'widget'))

        from django.contrib.auth.forms import ReadOnlyPasswordHashField
        self.assertIsInstance(form.fields['password'], ReadOnlyPasswordHashField)

    def test_form_change_phone_to_existing(self):
        User.objects.create_user(phone='09987654321', password='pass123')

        data = self.valid_data.copy()
        data['phone'] = '09987654321'
        form = UserChangeForm(instance=self.user, data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_form_deactivate_user(self):
        data = self.valid_data.copy()
        data['is_active'] = False
        form = UserChangeForm(instance=self.user, data=data)
        self.assertTrue(form.is_valid())
        updated_user = form.save()
        self.assertFalse(updated_user.is_active)

    def test_form_make_admin(self):
        data = self.valid_data.copy()
        data['is_admin'] = True
        form = UserChangeForm(instance=self.user, data=data)
        self.assertTrue(form.is_valid())
        updated_user = form.save()
        self.assertTrue(updated_user.is_admin)
        self.assertTrue(updated_user.is_staff)

    def test_form_remove_email(self):
        data = self.valid_data.copy()
        data['email'] = ''
        form = UserChangeForm(instance=self.user, data=data)
        self.assertTrue(form.is_valid())
        updated_user = form.save()
        self.assertEqual(updated_user.email, None)

    def test_form_fields_present(self):
        form = UserChangeForm(instance=self.user)
        expected_fields = [
            'phone', 'first_name', 'last_name', 'email',
            'is_active', 'is_admin', 'groups', 'user_permissions', 'password'
        ]
        for field in expected_fields:
            self.assertIn(field, form.fields)


class TestSignInSignUpForm(TestCase):
    def test_valid_form(self):
        data = {'phone': '09123456789', 'email': 'test@example.com'}
        form = SignInSignUpForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_phone_length(self):
        data = {'phone': '0912345678', 'email': 'test@example.com'}
        form = SignInSignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_invalid_phone_format_not_start_with_09(self):
        data = {'phone': '08123456789', 'email': 'test@example.com'}
        form = SignInSignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_invalid_phone_with_letters(self):
        data = {'phone': '09123abc789', 'email': 'test@example.com'}
        form = SignInSignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_invalid_email(self):
        data = {'phone': '09123456789', 'email': 'invalid_email'}
        form = SignInSignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_missing_fields(self):
        data = {}
        form = SignInSignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        self.assertIn('email', form.errors)
