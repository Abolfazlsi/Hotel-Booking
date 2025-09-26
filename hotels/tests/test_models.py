from django.test import TestCase
from hotels.models import Room, Service, Review, RoomImage
from accounts.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Avg, Count
from django.utils.text import slugify
from unittest.mock import patch, PropertyMock
import jdatetime
from datetime import datetime
from datetime import timedelta
import jdatetime
from django.utils import timezone


class TestServiceModel(TestCase):
    def test_create_service(self):
        service = Service.objects.create(name='WiFi')
        self.assertEqual(service.name, 'WiFi')
        self.assertEqual(str(service), 'WiFi')


class TestRoomModel(TestCase):
    def setUp(self):
        self.service = Service.objects.create(name='WiFi')

    def test_create_room(self):
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        room.services.add(self.service)
        self.assertEqual(room.title, 'Test Room')
        self.assertEqual(room.price, 100000)
        self.assertEqual(room.size, 50)
        self.assertEqual(room.capacity, 2)
        self.assertEqual(room.description, 'Test description')
        self.assertTrue(room.existing)
        self.assertEqual(room.services.count(), 1)
        self.assertEqual(str(room), 'Test Room')

    def test_save_generates_slug(self):
        room = Room.objects.create(
            title='اتاق تست',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.assertEqual(room.slug, slugify('اتاق تست', allow_unicode=True))

    def test_get_absolute_url(self):
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.assertEqual(room.get_absolute_url(), reverse('hotels:room_detail', args=[room.slug]))

    def test_get_rating_no_reviews(self):
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.assertEqual(room.get_rating(), 0.0)

    @patch('hotels.models.Room.reviews')
    def test_get_rating_with_reviews(self, mock_reviews):
        mock_reviews.aggregate.return_value = {'rating__avg': 4.5}
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.assertEqual(room.get_rating(), 4.5)

    def test_get_rating_breakdown_no_reviews(self):
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.assertEqual(room.get_rating_breakdown(), {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0})

    @patch('hotels.models.Room.reviews')
    def test_get_rating_breakdown_with_reviews(self, mock_reviews):
        mock_reviews.count.return_value = 10
        mock_reviews.values.return_value.annotate.return_value.order_by.return_value = [
            {'rating': 5, 'count': 6},
            {'rating': 4, 'count': 4}
        ]
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        breakdown = room.get_rating_breakdown()
        self.assertEqual(breakdown['5'], 60.0)
        self.assertEqual(breakdown['4'], 40.0)
        self.assertEqual(breakdown['3'], 0)

    @patch('hotels.models.Room.images')
    def test_primary_image(self, mock_images):
        mock_images.filter.return_value.first.return_value = 'test_image'
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        self.assertEqual(room.primary_image, 'test_image')

    def test_created_at_jalali(self):
        room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )
        room.created_at = datetime(2025, 1, 1, 12, 0, 0)
        room.save()
        jalali_date = jdatetime.datetime.fromgregorian(datetime=room.created_at)
        self.assertEqual(room.created_at_jalali(), jalali_date.strftime('%Y/%m/%d %H:%M:%S'))

    def test_price_validator(self):
        with self.assertRaises(ValidationError):
            room = Room(
                title='Test Room',
                price=-1,
                size=50,
                capacity=2,
                description='Test description',
                existing=True
            )
            room.full_clean()


class TestRoomImageModel(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            title='Test Room',
            price=100000,
            size=50,
            capacity=2,
            description='Test description',
            existing=True
        )

    def test_create_room_image(self):
        room_image = RoomImage.objects.create(
            room=self.room,
            image='test.jpg',
            alt_text='Test alt text',
            is_primary=True
        )
        self.assertEqual(room_image.room, self.room)
        self.assertEqual(room_image.alt_text, 'Test alt text')
        self.assertTrue(room_image.is_primary)
        self.assertEqual(str(room_image), 'Test Room')

    def test_default_is_primary(self):
        room_image = RoomImage.objects.create(
            room=self.room,
            image='test.jpg',
            alt_text='Test alt text'
        )
        self.assertFalse(room_image.is_primary)

    def test_relationship_with_room(self):
        room_image = RoomImage.objects.create(
            room=self.room,
            image='test.jpg',
            alt_text='Test alt text'
        )
        self.assertIn(room_image, self.room.images.all())


class ReviewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09111111111',
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
        self.review = Review.objects.create(
            room=self.room,
            user=self.user,
            rating=4,
            comment='Great room!',
            is_featured=True
        )

    def test_review_creation(self):
        self.assertEqual(self.review.room.title, 'Test Room')
        self.assertEqual(self.review.user.phone, '09111111111')
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.comment, 'Great room!')
        self.assertTrue(self.review.is_featured)
        self.assertIsNotNone(self.review.created_at)

    def test_rating_validation_min(self):
        invalid_review = Review(room=self.room, user=self.user, rating=0, comment='Invalid')
        with self.assertRaises(ValidationError):
            invalid_review.full_clean()

    def test_rating_validation_max(self):
        invalid_review = Review(room=self.room, user=self.user, rating=6, comment='Invalid')
        with self.assertRaises(ValidationError):
            invalid_review.full_clean()

    def test_str_method(self):
        expected = f" {self.user.first_name} {self.user.last_name} --> {self.room}"
        self.assertEqual(str(self.review), expected)

    def test_get_rating_given_range(self):
        self.assertEqual(list(self.review.get_rating_given_range), [0, 1, 2, 3])

    def test_time_since_creation_seconds(self):
        review = Review.objects.create(room=self.room, user=self.user, rating=3, comment='Test')
        review.created_at = timezone.now() - timedelta(seconds=30)
        review.save()
        self.assertEqual(review.time_since_creation(), '30 ثانیه پیش')

    def test_time_since_creation_minutes(self):
        review = Review.objects.create(room=self.room, user=self.user, rating=3, comment='Test')
        review.created_at = timezone.now() - timedelta(minutes=6)
        review.save()
        self.assertEqual(review.time_since_creation(), '6 دقیقه پیش')

    def test_time_since_creation_hours(self):
        review = Review.objects.create(room=self.room, user=self.user, rating=3, comment='Test')
        review.created_at = timezone.now() - timedelta(hours=2)
        review.save()
        self.assertEqual(review.time_since_creation(), '2 ساعت پیش')

    def test_time_since_creation_days(self):
        review = Review.objects.create(room=self.room, user=self.user, rating=3, comment='Test')
        review.created_at = timezone.now() - timedelta(days=3)
        review.save()
        self.assertEqual(review.time_since_creation(), '3 روز پیش')

    def test_time_since_creation_months(self):
        review = Review.objects.create(room=self.room, user=self.user, rating=3, comment='Test')
        review.created_at = timezone.now() - timedelta(days=45)
        review.save()
        self.assertEqual(review.time_since_creation(), '1 ماه پیش')

    def test_time_since_creation_years(self):
        review = Review.objects.create(room=self.room, user=self.user, rating=3, comment='Test')
        review.created_at = timezone.now() - timedelta(days=400)
        review.save()
        self.assertEqual(review.time_since_creation(), '1 سال پیش')

    def test_created_at_jalali(self):
        review = Review.objects.create(room=self.room, user=self.user, rating=3, comment='Test')
        review.created_at = datetime(2025, 1, 1, 12, 0, 0)
        review.save()
        jalali_date = jdatetime.datetime.fromgregorian(datetime=review.created_at)
        expected = jalali_date.strftime('%Y/%m/%d %H:%M:%S')
        self.assertEqual(review.created_at_jalali(), expected)

