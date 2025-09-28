from django.test import TestCase
from reservations.models import Booking, Guest, Transaction
from hotels.models import Room, Service
from accounts.models import User
from datetime import date, timedelta
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError


class BookingModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.user2 = User.objects.create_user(
            phone='09987654321',
            password='testpass456',
        )

        self.room1 = Room.objects.create(
            title="اتاق دو تخته",
            price=500000,
            size=30,
            capacity=2,
            description="اتاق دو تخته استاندارد"
        )

        self.room2 = Room.objects.create(
            title="سوئیت",
            price=1000000,
            size=50,
            capacity=4,
            description="سوئیت لوکس"
        )

        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)

    def test_create_booking_success(self):
        booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=2,
            nights_stay=6
        )

        self.assertEqual(booking.status, 'pending')
        self.assertEqual(booking.total_price, 3000000)
        self.assertEqual(booking.nights(), 6)

    def test_booking_def_str(self):
        user_no_name = User.objects.create_user(
            phone='09111111111',
            password='testpass'
        )

        booking = Booking.objects.create(
            user=user_no_name,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=1,
            nights_stay=6
        )

        expected_str = "رزرو اتاق دو تخته توسط 09111111111 "
        self.assertEqual(str(booking), expected_str)

    def test_nights_calculation(self):
        booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.today,
            check_out=self.today + timedelta(days=3),
            people_count=2,
        )

        self.assertEqual(booking.nights(), 3)

    def test_nights_with_null_dates(self):
        booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=None,
            check_out=None,
            people_count=2,
        )

        self.assertEqual(booking.nights(), 0)

    def test_clean_check_out_before_check_in(self):
        booking = Booking(
            user=self.user1,
            room=self.room1,
            check_in=self.next_week,
            check_out=self.tomorrow,
            people_count=2,
            nights_stay=1
        )

        with self.assertRaises(ValidationError) as context:
            booking.clean()

        self.assertIn("تاریخ خروج باید بعد از تاریخ ورود باشد", context.exception.messages[0])

    def test_clean_people_count_exceeds_capacity(self):
        booking = Booking(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=3,
            nights_stay=6
        )

        with self.assertRaises(ValidationError) as context:
            booking.clean()

        error_message = context.exception.messages[0]
        self.assertIn("تعداد نفرات", error_message)
        self.assertIn("ظرفیت اتاق", error_message)
        self.assertIn("(2)", error_message)

    def test_clean_conflicting_bookings(self):
        existing_booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=2,
            status='confirmed',
            nights_stay=6
        )

        new_booking = Booking(
            user=self.user2,
            room=self.room1,
            check_in=self.tomorrow + timedelta(days=2),
            check_out=self.tomorrow + timedelta(days=4),
            people_count=2,
            nights_stay=2
        )

        with self.assertRaises(ValidationError) as context:
            new_booking.clean()

        error_message = context.exception.messages[0]
        self.assertIn("اتاق", error_message)
        self.assertIn("دسترس", error_message)

    def test_save_calculates_total_price(self):
        booking = Booking(
            user=self.user1,
            room=self.room1,
            check_in=self.today,
            check_out=self.today + timedelta(days=5),
            people_count=2,
            nights_stay=5
        )
        booking.save()

        self.assertEqual(booking.total_price, 2500000)

    def test_save_confirmed_booking_updates_room_availability(self):
        self.assertTrue(self.room1.existing)

        booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=2,
            status='confirmed',
            nights_stay=6
        )

        self.room1.refresh_from_db()
        self.assertFalse(self.room1.existing)

    def test_save_canceled_booking_restores_room_availability(self):
        booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=2,
            status='confirmed',
            nights_stay=6
        )

        self.room1.refresh_from_db()
        self.assertFalse(self.room1.existing)

        booking.status = 'canceled'
        booking.save()

        self.room1.refresh_from_db()
        self.assertTrue(self.room1.existing)

    def test_canceled_booking_with_other_confirmed_bookings(self):
        booking1 = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.tomorrow + timedelta(days=3),
            people_count=2,
            status='confirmed',
            nights_stay=3
        )

        booking2 = Booking.objects.create(
            user=self.user2,
            room=self.room1,
            check_in=self.tomorrow + timedelta(days=5),
            check_out=self.tomorrow + timedelta(days=8),
            people_count=2,
            status='confirmed',
            nights_stay=3
        )

        self.room1.refresh_from_db()
        self.assertFalse(self.room1.existing)

        booking1.status = 'canceled'
        booking1.save()

        self.room1.refresh_from_db()
        self.assertFalse(self.room1.existing)

    def test_status_choices(self):
        booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=2,
            nights_stay=6
        )

        valid_statuses = ['pending', 'confirmed', 'canceled']
        for status in valid_statuses:
            booking.status = status
            booking.save()
            self.assertEqual(booking.status, status)

    def test_same_day_checkout(self):
        booking = Booking(
            user=self.user1,
            room=self.room1,
            check_in=self.today,
            check_out=self.today,
            people_count=2,
            nights_stay=0
        )

        with self.assertRaises(ValidationError):
            booking.clean()

    def test_concurrent_booking_creation(self):
        booking1 = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.tomorrow + timedelta(days=2),
            people_count=2,
            status='pending',
            nights_stay=2
        )

        booking2 = Booking(
            user=self.user2,
            room=self.room1,
            check_in=self.tomorrow + timedelta(days=1),
            check_out=self.tomorrow + timedelta(days=3),
            people_count=2,
            status='pending',
            nights_stay=2
        )

        with self.assertRaises(ValidationError):
            booking2.clean()

    def test_multiple_validation_errors(self):
        existing_booking = Booking.objects.create(
            user=self.user1,
            room=self.room1,
            check_in=self.tomorrow,
            check_out=self.next_week,
            people_count=2,
            status='confirmed',
            nights_stay=6
        )

        invalid_booking = Booking(
            user=self.user2,
            room=self.room1,
            check_in=self.next_week,
            check_out=self.tomorrow,
            people_count=6,
            nights_stay=1
        )

        with self.assertRaises(ValidationError) as context:
            invalid_booking.clean()

        errors = context.exception.messages
        self.assertTrue(any("تاریخ خروج" in error for error in errors))


class GuestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            password='12345',
        )
        self.room = Room.objects.create(
            title='Test Room',
            price=100,
            size=20,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in='2023-10-01',
            check_out='2023-10-05',
            people_count=2,
            status='pending'
        )
        self.guest = Guest.objects.create(
            booking=self.booking,
            full_name='Abolfazl Shojaie',
            national_id='1234567890',
            phone_number='09123456789',
            gender='F'
        )

    def test_guest_create(self):
        self.assertEqual(self.guest.booking, self.booking)
        self.assertEqual(self.guest.full_name, 'Abolfazl Shojaie')
        self.assertEqual(self.guest.national_id, '1234567890')
        self.assertEqual(self.guest.phone_number, '09123456789')
        self.assertEqual(self.guest.gender, 'F')

    def test_str_method(self):
        self.assertEqual(str(self.guest), f"Abolfazl Shojaie --> {self.booking}")

    def test_national_id_validation_invalid_length(self):
        invalid_guest = Guest(
            booking=self.booking,
            full_name='Invalid',
            national_id='123456789',
            phone_number='09123456789',
            gender='M'
        )
        with self.assertRaises(ValidationError):
            invalid_guest.full_clean()

    def test_national_id_validation_non_numeric(self):
        invalid_guest = Guest(
            booking=self.booking,
            full_name='Invalid',
            national_id='123456789a',
            phone_number='09123456789',
            gender='M'
        )
        with self.assertRaises(ValidationError):
            invalid_guest.full_clean()

    def test_phone_number_validation_invalid_format(self):
        invalid_guest = Guest(
            booking=self.booking,
            full_name='Invalid',
            national_id='1234567890',
            phone_number='08123456789',
            gender='M'
        )
        with self.assertRaises(ValidationError):
            invalid_guest.full_clean()

    def test_phone_number_validation_invalid_length(self):
        invalid_guest = Guest(
            booking=self.booking,
            full_name='Invalid',
            national_id='1234567890',
            phone_number='0912345678',
            gender='M'
        )
        with self.assertRaises(ValidationError):
            invalid_guest.full_clean()

    def test_gender_choices(self):
        self.guest.gender = 'M'
        self.guest.full_clean()
        self.guest.gender = 'F'
        self.guest.full_clean()
        self.guest.gender = 'X'
        with self.assertRaises(ValidationError):
            self.guest.full_clean()

    def test_booking_required(self):
        with self.assertRaises(IntegrityError):
            Guest.objects.create(
                full_name='None',
                national_id='1234567890',
                phone_number='09123456789',
                gender='F'
            )


class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            password='12345',
        )
        self.room = Room.objects.create(
            title='Test Room',
            price=100,
            size=20,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.booking = Booking.objects.create(
            user=self.user,
            room=self.room,
            check_in='2023-10-01',
            check_out='2023-10-05',
            people_count=2,
            status='pending'
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            booking=self.booking,
            amount=500,
            transaction_id='TX123456',
            status='success'
        )

    def test_transaction_creation(self):
        self.assertEqual(self.transaction.user, self.user)
        self.assertEqual(self.transaction.booking, self.booking)
        self.assertEqual(self.transaction.amount, 500)
        self.assertEqual(self.transaction.transaction_id, 'TX123456')
        self.assertEqual(self.transaction.status, 'success')
        self.assertIsNotNone(self.transaction.created_at)

    def test_str_method_with_booking(self):
        self.assertEqual(str(self.transaction), f"تراکنش TX123456 برای {self.booking}")

    def test_str_method_without_booking(self):
        transaction_no_booking = Transaction.objects.create(
            user=self.user,
            amount=300,
            transaction_id='TX654321',
            status='failed'
        )
        self.assertEqual(str(transaction_no_booking), "تراکنش TX654321 برای بدون رزرو")

    def test_amount_validation_negative(self):
        invalid_transaction = Transaction(
            user=self.user,
            amount=-100,
            transaction_id='TXINVALID',
            status='failed'
        )
        with self.assertRaises(ValidationError):
            invalid_transaction.full_clean()

    def test_transaction_id_unique(self):
        with self.assertRaises(IntegrityError):
            Transaction.objects.create(
                user=self.user,
                amount=200,
                transaction_id='TX123456',
                status='success'
            )

    def test_status_choices(self):
        self.transaction.status = 'success'
        self.transaction.full_clean()
        self.transaction.status = 'failed'
        self.transaction.full_clean()
        self.transaction.status = 'invalid'
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()

    def test_user_required(self):
        with self.assertRaises(IntegrityError):
            Transaction.objects.create(
                amount=100,
                transaction_id='TXUSERLESS',
                status='failed'
            )

    def test_booking_optional(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=400,
            transaction_id='TXNOBKG',
            status='success'
        )
        self.assertIsNone(transaction.booking)
