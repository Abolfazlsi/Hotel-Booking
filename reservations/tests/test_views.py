from django.test import TestCase, Client, override_settings
from django.urls import reverse
from unittest.mock import patch
from reservations.models import Booking, Guest, Transaction
from hotels.models import Room, Service
from reservations.views import SendRequestView, VerifyView
import jdatetime
import json
from accounts.models import User
from unittest.mock import patch, Mock
import requests
import jdatetime
from datetime import date, timedelta
from django.db import IntegrityError


class SendRequestViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.room = Room.objects.create(
            title="اتاق دو تخته",
            price=500000,
            size=30,
            capacity=2,
            description="اتاق دو تخته استاندارد"
        )

        self.url = reverse('reservations:send-request', kwargs={'slug': self.room.slug})

        today = jdatetime.date.today()
        self.check_in = (today + jdatetime.timedelta(days=1)).strftime('%Y/%m/%d')
        self.check_out = (today + jdatetime.timedelta(days=3)).strftime('%Y/%m/%d')

        self.valid_guest_data = {
            'capacity': '2',
            'check_in': self.check_in,
            'check_out': self.check_out,
            'guest_1-full_name': 'علی احمدی',
            'guest_1-national_id': '1234567890',
            'guest_1-phone_number': '09123456789',
            'guest_1-gender': 'M',
            'guest_2-full_name': 'مریم محمدی',
            'guest_2-national_id': '0987654321',
            'guest_2-phone_number': '09987654321',
            'guest_2-gender': 'F',
        }

    def test_post_not_authenticated(self):
        response = self.client.post(self.url, self.valid_guest_data)
        self.assertEqual(response.status_code, 302)

    @patch('requests.post')
    def test_successful_reservation(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'code': 100,
                'authority': 'test_authority_123'
            }
        }
        mock_post.return_value = mock_response

        self.client.login(phone='09123456789', password='testpass123')
        response = self.client.post(self.url, self.valid_guest_data)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('redirect_url', data)
        self.assertIn('test_authority_123', data['redirect_url'])

        session = self.client.session
        self.assertEqual(session['authority'], 'test_authority_123')
        self.assertIn('reservation_data', session)
        self.assertEqual(session['reservation_data']['room_slug'], self.room.slug)
        self.assertEqual(session['reservation_data']['capacity'], 2)
        self.assertEqual(session['reservation_data']['total_price'], 1000000)
        self.assertEqual(session['reservation_data']['nights'], 2)

    def test_invalid_check_out_before_check_in(self):
        self.client.login(phone='09123456789', password='testpass123')

        invalid_data = self.valid_guest_data.copy()
        invalid_data['check_out'] = invalid_data['check_in']

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('dates', data['errors'])

    def test_invalid_date_format(self):
        self.client.login(phone='09123456789', password='testpass123')

        invalid_data = self.valid_guest_data.copy()
        invalid_data['check_in'] = 'invalid-date'

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('dates', data['errors'])

    def test_capacity_mismatch(self):
        self.client.login(phone='09123456789', password='testpass123')

        invalid_data = self.valid_guest_data.copy()
        invalid_data['capacity'] = '3'

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('capacity', data['errors'])

    def test_invalid_guest_data(self):
        self.client.login(phone='09123456789', password='testpass123')

        invalid_data = self.valid_guest_data.copy()
        invalid_data['guest_1-national_id'] = '123'  # Invalid national ID

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('guests', data['errors'])

    def test_room_already_booked(self):
        self.client.login(phone='09123456789', password='testpass123')

        check_in_jalali = jdatetime.datetime.strptime(self.check_in, '%Y/%m/%d').date()
        check_out_jalali = jdatetime.datetime.strptime(self.check_out, '%Y/%m/%d').date()

        existing_booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in=check_in_jalali.togregorian(),
            check_out=check_out_jalali.togregorian(),
            people_count=2,
            status='confirmed',
            nights_stay=2
        )

        response = self.client.post(self.url, self.valid_guest_data)

        self.assertEqual(response.status_code, 409)
        self.assertIn('متاسفانه این اتاق', response.content.decode())

    @patch('requests.post')
    def test_payment_gateway_error(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'code': 101
            },
            'errors': {
                'message': 'خطا در پردازش'
            }
        }
        mock_post.return_value = mock_response

        self.client.login(phone='09123456789', password='testpass123')
        response = self.client.post(self.url, self.valid_guest_data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('خطا در پردازش', response.content.decode())

    @patch('requests.post')
    def test_network_error(self, mock_post):
        mock_post.side_effect = requests.RequestException("Network error")

        self.client.login(phone='09123456789', password='testpass123')
        response = self.client.post(self.url, self.valid_guest_data)

        self.assertEqual(response.status_code, 500)
        self.assertIn('خطای شبکه', response.content.decode())

    def test_room_not_found(self):
        self.client.login(phone='09123456789', password='testpass123')

        url = reverse('reservations:send-request', kwargs={'slug': 'non-existent-room'})
        response = self.client.post(url, self.valid_guest_data)

        self.assertEqual(response.status_code, 404)

    def test_session_data_storage(self):
        self.client.login(phone='09123456789', password='testpass123')

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'data': {
                    'code': 100,
                    'authority': 'test_auth'
                }
            }
            mock_post.return_value = mock_response

            response = self.client.post(self.url, self.valid_guest_data)

            session = self.client.session
            reservation_data = session['reservation_data']

            self.assertEqual(len(reservation_data['guests']), 2)
            self.assertEqual(reservation_data['guests'][0]['full_name'], 'علی احمدی')
            self.assertEqual(reservation_data['guests'][1]['full_name'], 'مریم محمدی')

    def test_minimum_one_night_stay(self):
        self.client.login(phone='09123456789', password='testpass123')

        today = jdatetime.date.today()
        same_day_data = self.valid_guest_data.copy()
        same_day_data['check_in'] = today.strftime('%Y/%m/%d')
        same_day_data['check_out'] = today.strftime('%Y/%m/%d')

        response = self.client.post(self.url, same_day_data)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('حداقل یک شب اقامت لازم است', data['errors']['dates'])


class VerifyViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.room = Room.objects.create(
            title="اتاق دو تخته",
            price=500000,
            size=30,
            capacity=2,
            description="اتاق دو تخته استاندارد"
        )

        self.url = reverse('reservations:payment-verify')

        today = jdatetime.date.today()
        self.check_in = today + jdatetime.timedelta(days=1)
        self.check_out = today + jdatetime.timedelta(days=3)

        self.reservation_data = {
            'room_slug': self.room.slug,
            'check_in': self.check_in.isoformat(),
            'check_out': self.check_out.isoformat(),
            'capacity': 2,
            'total_price': 1000000,
            'nights': 2,
            'guests': [
                {
                    'full_name': 'علی احمدی',
                    'national_id': '1234567890',
                    'phone_number': '09123456789',
                    'gender': 'M'
                },
                {
                    'full_name': 'مریم محمدی',
                    'national_id': '0987654321',
                    'phone_number': '09987654321',
                    'gender': 'F'
                }
            ]
        }

        session = self.client.session
        session['authority'] = 'test_authority_123'
        session['reservation_data'] = self.reservation_data
        session.save()

    def test_get_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url, {'Status': 'OK', 'Authority': 'test_authority_123'})
        self.assertEqual(response.status_code, 302)

    def test_missing_parameters(self):
        self.client.login(phone='09123456789', password='testpass123')

        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('reservations:payment-fail'))

        response = self.client.get(self.url, {'Status': 'OK'})
        self.assertRedirects(response, reverse('reservations:payment-fail'))

        response = self.client.get(self.url, {'Authority': 'test_authority_123'})
        self.assertRedirects(response, reverse('reservations:payment-fail'))

    def test_authority_mismatch(self):
        self.client.login(phone='09123456789', password='testpass123')

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'different_authority'
        })

        self.assertRedirects(response, reverse('reservations:payment-fail'))

    def test_missing_session_data(self):
        self.client.login(phone='09123456789', password='testpass123')

        session = self.client.session
        session.pop('reservation_data', None)
        session.save()

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.assertRedirects(response, reverse('reservations:payment-fail'))

    @patch('requests.post')
    @override_settings(MERCHANT='test_merchant')
    def test_successful_payment_verification(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'code': 100
            }
        }
        mock_post.return_value = mock_response

        self.client.login(phone='09123456789', password='testpass123')

        initial_booking_count = Booking.objects.count()
        initial_guest_count = Guest.objects.count()
        initial_transaction_count = Transaction.objects.count()

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.assertEqual(Booking.objects.count(), initial_booking_count + 1)
        self.assertEqual(Guest.objects.count(), initial_guest_count + 2)
        self.assertEqual(Transaction.objects.count(), initial_transaction_count + 1)

        booking = Booking.objects.latest('created_at')
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.room, self.room)
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(booking.total_price, 1000000)
        self.assertEqual(booking.nights_stay, 2)
        self.assertEqual(booking.people_count, 2)

        guests = Guest.objects.filter(booking=booking)
        self.assertEqual(guests.count(), 2)
        guest_names = [guest.full_name for guest in guests]
        self.assertIn('علی احمدی', guest_names)
        self.assertIn('مریم محمدی', guest_names)

        trans = Transaction.objects.latest('created_at')
        self.assertEqual(trans.user, self.user)
        self.assertEqual(trans.amount, 1000000)
        self.assertEqual(trans.status, 'success')
        self.assertEqual(trans.booking, booking)
        self.assertEqual(trans.transaction_id, 'test_authority_123')

        self.assertRedirects(response, reverse('reservations:payment-success', kwargs={'pk': booking.id}))

        session = self.client.session
        self.assertNotIn('reservation_data', session)
        self.assertNotIn('authority', session)

    @patch('requests.post')
    def test_payment_verification_failed(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'code': 102
            }
        }
        mock_post.return_value = mock_response

        self.client.login(phone='09123456789', password='testpass123')

        initial_transaction_count = Transaction.objects.count()

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.assertEqual(Transaction.objects.count(), initial_transaction_count + 1)

        trans = Transaction.objects.latest('created_at')
        self.assertEqual(trans.status, 'failed')
        self.assertIsNone(trans.booking)

        self.assertRedirects(response, reverse('reservations:payment-fail'))

    def test_payment_status_not_ok(self):
        self.client.login(phone='09123456789', password='testpass123')

        initial_transaction_count = Transaction.objects.count()

        response = self.client.get(self.url, {
            'Status': 'NOK',
            'Authority': 'test_authority_123'
        })

        self.assertEqual(Transaction.objects.count(), initial_transaction_count + 1)

        trans = Transaction.objects.latest('created_at')
        self.assertEqual(trans.status, 'failed')

        self.assertRedirects(response, reverse('reservations:payment-fail'))

    @patch('requests.post')
    def test_network_error_during_verification(self, mock_post):
        mock_post.side_effect = requests.RequestException("Network error")

        self.client.login(phone='09123456789', password='testpass123')

        initial_transaction_count = Transaction.objects.count()

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.assertEqual(Transaction.objects.count(), initial_transaction_count + 1)

        trans = Transaction.objects.latest('created_at')
        self.assertEqual(trans.status, 'failed')

        self.assertRedirects(response, reverse('reservations:payment-fail'))

    def test_price_manipulation_detection(self):
        self.client.login(phone='09123456789', password='testpass123')

        session = self.client.session
        tampered_data = self.reservation_data.copy()
        tampered_data['total_price'] = 500000
        session['reservation_data'] = tampered_data
        session.save()

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.assertRedirects(response, reverse('reservations:payment-fail'))

    def test_invalid_date_format(self):
        self.client.login(phone='09123456789', password='testpass123')

        session = self.client.session
        invalid_data = self.reservation_data.copy()
        invalid_data['check_in'] = 'invalid-date'
        session['reservation_data'] = invalid_data
        session.save()

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.assertRedirects(response, reverse('reservations:payment-fail'))

    def test_room_not_found(self):
        self.client.login(phone='09123456789', password='testpass123')

        session = self.client.session
        invalid_data = self.reservation_data.copy()
        invalid_data['room_slug'] = 'non-existent-room'
        session['reservation_data'] = invalid_data
        session.save()

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.assertEqual(response.status_code, 404)

    @patch('requests.post')
    def test_database_error_during_booking_creation(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'code': 100
            }
        }
        mock_post.return_value = mock_response

        self.client.login(phone='09123456789', password='testpass123')

        with patch('reservations.models.Booking.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")

            initial_transaction_count = Transaction.objects.count()

            response = self.client.get(self.url, {
                'Status': 'OK',
                'Authority': 'test_authority_123'
            })

            self.assertEqual(Transaction.objects.count(), initial_transaction_count + 1)

            trans = Transaction.objects.latest('created_at')
            self.assertEqual(trans.status, 'failed')

            self.assertRedirects(response, reverse('reservations:payment-fail'))

    def test_cleanup_session_method(self):
        self.client.login(phone='09123456789', password='testpass123')

        view = VerifyView()
        request = self.client.get(self.url).wsgi_request
        request.session['reservation_data'] = self.reservation_data
        request.session['authority'] = 'test_authority'

        view.cleanup_session(request)

        self.assertNotIn('reservation_data', request.session)
        self.assertNotIn('authority', request.session)
        self.assertTrue(request.session.modified)

    @patch('requests.post')
    def test_room_availability_update_on_confirmed_booking(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'code': 100
            }
        }
        mock_post.return_value = mock_response

        self.client.login(phone='09123456789', password='testpass123')

        self.assertTrue(self.room.existing)

        response = self.client.get(self.url, {
            'Status': 'OK',
            'Authority': 'test_authority_123'
        })

        self.room.refresh_from_db()
        self.assertFalse(self.room.existing)

    def test_duplicate_transaction_id_handling(self):
        existing_trans = Transaction.objects.create(
            user=self.user,
            amount=500000,
            transaction_id='test_authority_123',
            status='success'
        )

        self.client.login(phone='09123456789', password='testpass123')

        with self.assertRaises(IntegrityError):
            response = self.client.get(self.url, {
                'Status': 'NOK',
                'Authority': 'test_authority_123'
            })


class PaymentSuccessViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(phone='09123456789', password='12345')
        self.user2 = User.objects.create_user(phone='09876543210', password='54321')
        self.room = Room.objects.create(
            title='Test Room',
            price=100,
            size=20,
            capacity=2,
            description='Test Desc',
            existing=True
        )
        self.booking1 = Booking.objects.create(
            user=self.user1,
            room=self.room,
            check_in='2023-10-01',
            check_out='2023-10-05',
            people_count=2,
            status='confirmed'
        )
        self.booking2 = Booking.objects.create(
            user=self.user2,
            room=self.room,
            check_in='2023-11-01',
            check_out='2023-11-05',
            people_count=2,
            status='confirmed'
        )
        self.url1 = reverse('reservations:payment-success', kwargs={'pk': self.booking1.pk})
        self.url2 = reverse('reservations:payment-success', kwargs={'pk': self.booking2.pk})

    def test_required_login(self):
        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/accounts/signin-signup/?next={self.url1}')

    def test_view_correct_template(self):
        self.client.login(phone='09123456789', password='12345')
        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reservations/payment_success.html')

    def test_view_displays_own_booking(self):
        self.client.login(phone='09123456789', password='12345')
        response = self.client.get(self.url1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.booking1)

    def test_view_404_for_other_user_booking(self):
        self.client.login(phone='09123456789', password='12345')
        response = self.client.get(self.url2)
        self.assertEqual(response.status_code, 404)

    def test_view_404_for_not_exist_booking(self):
        self.client.login(phone='09123456789', password='12345')
        nonexistent_url = reverse('reservations:payment-success', kwargs={'pk': 12})
        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, 404)
