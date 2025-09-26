from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.conf import settings
from unittest.mock import patch, MagicMock
import secrets
import redis
from accounts.views import SignInSignUpView, OtpVerifyView
from accounts.forms import SignInSignUpForm, OtpVerifyForm, UserProfileForm
from accounts.models import User
from reservations.models import Booking
from hotels.models import Room
from datetime import date


class TestSignInSignUpView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('accounts:signin-signup')

    def test_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/singIn_singUp.html')
        self.assertIsInstance(response.context['form'], SignInSignUpForm)

    @patch('accounts.views.send_otp')
    @patch('accounts.views.redis_client')
    def test_post_valid_form(self, mock_redis, mock_send_otp):
        mock_redis.setex.return_value = True
        data = {'phone': '09123456789', 'email': 'test@example.com'}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('accounts:verify_otp'))
        self.assertIn('otp_token', self.client.session)
        self.assertIn('otp_phone', self.client.session)
        self.assertEqual(self.client.session['otp_phone'], '09123456789')
        mock_redis.setex.assert_called_once()
        mock_send_otp.assert_called_once()
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'کد تایید ارسال شد')

    @patch('accounts.views.send_otp')
    @patch('accounts.views.redis_client')
    def test_post_valid_form_redis_error(self, mock_redis, mock_send_otp):
        mock_redis.setex.side_effect = Exception('Redis error')
        data = {'phone': '09123456789', 'email': 'test@example.com'}
        response = self.client.post(self.url, data)
        self.assertTrue(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'مشکلی در اتصال پیش امده است')

    def test_post_invalid_form(self):
        data = {'phone': 'invalid', 'email': 'invalid'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/singIn_singUp.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'شماره تلفن نامعتبر است')


class TestOtpVerifyView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('accounts:verify_otp')

    def test_get_no_session_redirect(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('accounts:signin-signup'))

    def test_get_with_session(self):
        session = self.client.session
        session['otp_token'] = 'test_token'
        session.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/otp_verify.html')
        self.assertIsInstance(response.context['form'], OtpVerifyForm)

    @patch('accounts.views.redis_client')
    @patch('accounts.views.login')
    def test_post_valid_new_user(self, mock_login, mock_redis):
        mock_redis.get.return_value = b'1234'
        session = self.client.session
        session['otp_token'] = 'test_token'
        session['otp_phone'] = '09123456789'
        session.save()
        data = {'code': '1234'}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('hotels:home'))
        user = User.objects.get(phone='09123456789')
        mock_login.assert_called_once_with(response.wsgi_request, user,
                                           backend="django.contrib.auth.backends.ModelBackend")
        mock_redis.delete.assert_called_once_with("otp:09123456789:test_token")
        self.assertNotIn('otp_token', self.client.session)
        self.assertNotIn('otp_phone', self.client.session)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'ثبت نام با موفقیت انجام شد')

    @patch('accounts.views.redis_client')
    @patch('accounts.views.login')
    def test_post_valid_existing_user(self, mock_login, mock_redis):
        User.objects.create(phone='09123456789')
        mock_redis.get.return_value = b'1234'
        session = self.client.session
        session['otp_token'] = 'test_token'
        session['otp_phone'] = '09123456789'
        session.save()
        data = {'code': '1234'}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('hotels:home'))
        user = User.objects.get(phone='09123456789')
        mock_login.assert_called_once_with(response.wsgi_request, user,
                                           backend="django.contrib.auth.backends.ModelBackend")
        mock_redis.delete.assert_called_once_with("otp:09123456789:test_token")
        self.assertNotIn('otp_token', self.client.session)
        self.assertNotIn('otp_phone', self.client.session)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'ثبت نام با موفقیت انجام شد')

    @patch('accounts.views.redis_client')
    def test_post_invalid_code(self, mock_redis):
        mock_redis.get.return_value = b'5678'
        session = self.client.session
        session['otp_token'] = 'test_token'
        session['otp_phone'] = '09123456789'
        session.save()
        data = {'code': '1234'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/otp_verify.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'کد تایید نامعتبر است')

    def test_post_no_session(self):
        data = {'code': '1234'}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('accounts:signin-signup'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'مشکلی پیش امده است')

    @patch('accounts.views.redis_client')
    def test_post_redis_error(self, mock_redis):
        mock_redis.get.side_effect = Exception('Redis error')
        session = self.client.session
        session['otp_token'] = 'test_token'
        session['otp_phone'] = '09123456789'
        session.save()
        data = {'code': '1234'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/otp_verify.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'مشکلی در اتصال پیش امده است')

    def test_post_invalid_form(self):
        session = self.client.session
        session['otp_token'] = 'test_token'
        session['otp_phone'] = '09123456789'
        session.save()
        data = {'code': '123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/otp_verify.html')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'کد تایید نامعتبر است')


class TestLogOutView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('accounts:logout')
        self.user = User.objects.create_user(phone='09111111111', password='testpass')

    @patch('accounts.views.logout')
    def test_log_out_authenticated_user(self, mock_logout):
        self.client.login(phone='09111111111', password='testpass')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('hotels:home'))
        mock_logout.assert_called_once_with(response.wsgi_request)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'شما از حساب کاربری خود خارج شدید')

    def test_log_out_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("hotels:home"))


class TestUserProfileView(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('accounts:user_profile')
        self.user = User.objects.create(phone='09123456789')
        self.room = Room.objects.create(title='Test Room', price=100, size=50, capacity=2)
        Booking.objects.create(user=self.user, room=self.room, check_in=date(2023, 1, 1), check_out=date(2023, 1, 2),
                               people_count=2, status='confirmed', total_price=100000, nights_stay=1)
        self.client.force_login(self.user)

    def test_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertIsInstance(response.context['form'], UserProfileForm)
        self.assertEqual(response.context['form'].instance, self.user)
        self.assertEqual(len(response.context['booking']), 1)

    def test_post_valid_form(self):
        data = {'phone': '09123456789', 'first_name': 'Test', 'last_name': 'User', 'email': 'test@example.com'}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.email, 'test@example.com')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'اطلاعات حساب کاربری تغییر یافت.')

    def test_post_invalid_form(self):
        data = {'phone': 'invalid', 'first_name': 'Test', 'last_name': 'User', 'email': 'test@example.com'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertFalse(response.context['form'].is_valid())

    def test_get_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
