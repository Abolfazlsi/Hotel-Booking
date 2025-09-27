from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from hotels.models import Room, Service, Review, RoomImage
from django.core.files.uploadedfile import SimpleUploadedFile
from hotels.forms import SearchForm, ReviewForm, GuestForm
from datetime import date, timedelta
import jdatetime
from reservations.models import Booking
import json
from hotels.views import ReviewDeleteView


class HomePageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('hotels:home')

        self.service1 = Service.objects.create(name="WiFi")
        self.service2 = Service.objects.create(name="پارکینگ")
        self.service3 = Service.objects.create(name="صبحانه")

        self.user1 = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.user2 = User.objects.create_user(
            phone='09987654321',
            password='testpass456',
        )

        self.room_not_existing = Room.objects.create(
            title="اتاق اقتصادی",
            price=450000,
            size=20,
            capacity=1,
            description="اتاق تک نفره اقتصادی",
            existing=False
        )

        for i in range(1, 4):
            room = Room.objects.create(
                title=f"اتاق استاندارد {i}",
                price=600000 + (i * 50000),
                size=25 + i,
                capacity=2,
                description=f"اتاق استاندارد شماره {i} با امکانات کامل",
                existing=True
            )
            room.services.add(self.service1)

        self.room1 = Room.objects.create(
            title="اتاق دو تخته لوکس",
            price=850000,
            size=30,
            capacity=2,
            description="اتاق دو تخته با تمام امکانات رفاهی و منظره زیبا",
            existing=True
        )
        self.room1.services.add(self.service1, self.service2, self.service3)

        self.room2 = Room.objects.create(
            title="سوئیت رویال",
            price=2500000,
            size=75,
            capacity=4,
            description="سوئیت مجلل با دو اتاق خواب و پذیرایی",
            existing=True
        )
        self.room2.services.add(self.service1, self.service2)

        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'

        self.room_image1 = RoomImage.objects.create(
            room=self.room1,
            image=SimpleUploadedFile('room1.jpg', image_content, content_type='image/jpeg'),
            alt_text="تصویر اتاق دو تخته لوکس",
            is_primary=True
        )

        self.room_image2 = RoomImage.objects.create(
            room=self.room2,
            image=SimpleUploadedFile('room2.jpg', image_content, content_type='image/jpeg'),
            alt_text="تصویر سوئیت رویال",
            is_primary=True
        )

        self.review1 = Review.objects.create(
            room=self.room1,
            user=self.user1,
            rating=5,
            comment="اتاق فوق العاده بود، بسیار تمیز و مرتب",
            is_featured=True
        )

        self.review2 = Review.objects.create(
            room=self.room1,
            user=self.user2,
            rating=4,
            comment="اتاق خوبی بود ولی صدای بیرون کمی مزاحم بود",
            is_featured=False
        )

        self.review3 = Review.objects.create(
            room=self.room2,
            user=self.user1,
            rating=5,
            comment="بهترین سوئیتی که تا حالا اقامت داشتم",
            is_featured=True
        )

        for i in range(3, 6):
            Review.objects.create(
                room=self.room2,
                user=self.user2,
                rating=4,
                comment=f"نظر شماره {i}",
                is_featured=True
            )

    def test_homepage_loads_successfully(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hotels/index.html')

    def test_context_contains_rooms_list(self):
        response = self.client.get(self.url)
        self.assertIn('rooms_list', response.context)
        rooms_list = response.context['rooms_list']
        self.assertEqual(len(rooms_list), 5)

    def test_only_existing_rooms_displayed(self):
        response = self.client.get(self.url)
        rooms_list = response.context['rooms_list']
        room_titles = [room['title'] for room in rooms_list]
        self.assertNotIn("اتاق اقتصادی", room_titles)

    def test_room_datas(self):
        response = self.client.get(self.url)
        rooms_list = response.context['rooms_list']
        first_room = rooms_list[0]

        self.assertIn('title', first_room)
        self.assertIn('price', first_room)
        self.assertIn('capacity', first_room)
        self.assertIn('description', first_room)
        self.assertIn('image_url', first_room)
        self.assertIn('alt_text', first_room)
        self.assertIn('services', first_room)
        self.assertIn('url', first_room)
        self.assertIn('rating', first_room)

    def test_room_services(self):
        response = self.client.get(self.url)
        rooms_list = response.context['rooms_list']

        room_with_services = rooms_list[1]
        self.assertEqual(room_with_services['title'], "اتاق دو تخته لوکس")
        self.assertIn('WiFi', room_with_services['services'])
        self.assertIn('پارکینگ', room_with_services['services'])
        self.assertIn('صبحانه', room_with_services['services'])

    def test_room_rating(self):
        response = self.client.get(self.url)
        rooms_list = response.context['rooms_list']

        room_with_rating = rooms_list[1]
        self.assertEqual(room_with_rating['title'], "اتاق دو تخته لوکس")
        self.assertEqual(room_with_rating['rating'], 4.5)

        room_with_rating2 = rooms_list[0]
        self.assertEqual(room_with_rating2['title'], "سوئیت رویال")
        self.assertEqual(room_with_rating2['rating'], 4.25)

    def test_search_form_in_context(self):
        response = self.client.get(self.url)
        self.assertIn('search_form', response.context)
        self.assertIsInstance(response.context['search_form'], SearchForm)

    def test_featured_reviews_in_context(self):
        response = self.client.get(self.url)
        self.assertIn('featured_review', response.context)
        featured_reviews = response.context['featured_review']
        self.assertEqual(len(featured_reviews), 5)

    def test_only_featured_reviews_displayed(self):
        response = self.client.get(self.url)
        featured_reviews = response.context['featured_review']

        for review in featured_reviews:
            self.assertTrue(review.is_featured)


class RoomsListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('hotels:rooms_list')

        self.service1 = Service.objects.create(name="WiFi")
        self.service2 = Service.objects.create(name="پارکینگ")

        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.room1 = Room.objects.create(
            title="اتاق یک تخته",
            price=500000,
            size=20,
            capacity=1,
            description="اتاق یک تخته استاندارد"
        )
        self.room1.services.add(self.service1)

        self.room2 = Room.objects.create(
            title="اتاق دو تخته",
            price=800000,
            size=30,
            capacity=2,
            description="اتاق دو تخته لوکس"
        )
        self.room2.services.add(self.service1, self.service2)

        self.room3 = Room.objects.create(
            title="سوئیت",
            price=1500000,
            size=50,
            capacity=4,
            description="سوئیت خانوادگی"
        )
        self.room3.services.add(self.service1, self.service2)

        for i in range(4, 10):
            room = Room.objects.create(
                title=f"اتاق {i}",
                price=600000 + (i * 50000),
                size=25,
                capacity=2,
                description=f"اتاق شماره {i}"
            )
            room.services.add(self.service1)

    def test_rooms_list_view_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hotels/rooms.html')

    def test_pagination(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['room_list']), 5)

    def test_context_data(self):
        response = self.client.get(self.url)
        self.assertIn('services', response.context)
        self.assertIn('search_form', response.context)
        self.assertEqual(list(response.context['services']), [self.service1, self.service2])
        self.assertIsInstance(response.context['search_form'], SearchForm)

    def test_filter_by_capacity(self):
        response = self.client.get(self.url, {'people': '1'})
        room_list = response.context['room_list']
        self.assertEqual(len(room_list), 1)
        self.assertEqual(room_list[0].title, "اتاق یک تخته")

        response = self.client.get(self.url, {'people': '4'})
        room_list = response.context['room_list']
        self.assertEqual(len(room_list), 1)
        self.assertEqual(room_list[0].title, "سوئیت")

    def test_filter_by_price_range(self):
        response = self.client.get(self.url, {'min_price': '1000000'})
        room_list = response.context['room_list']
        filtered_rooms = [room for room in room_list if room.price >= 1000000]
        self.assertEqual(len(filtered_rooms), 3)

        response = self.client.get(self.url, {'max_price': '600000'})
        room_list = response.context['room_list']
        filtered_rooms = [room for room in room_list if room.price <= 600000]
        self.assertEqual(len(filtered_rooms), 1)
        self.assertEqual(filtered_rooms[0].title, "اتاق یک تخته")

        response = self.client.get(self.url, {'min_price': '700000', 'max_price': '900000'})
        all_rooms = Room.objects.filter(price__gte=700000, price__lte=900000)
        self.assertEqual(all_rooms.count(), 4)
        room_list = response.context['room_list']
        self.assertEqual(len(room_list), 4)

    def test_filter_by_date_availability(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        after_tomorrow = today + timedelta(days=2)

        booking = Booking.objects.create(
            user=self.user,
            room=self.room1,
            check_in=today,
            check_out=after_tomorrow,
            people_count=1,
            status='confirmed',
            total_price=1000000,
            nights_stay=2
        )

        today_j = jdatetime.date.fromgregorian(date=today)
        tomorrow_j = jdatetime.date.fromgregorian(date=tomorrow)

        response = self.client.get(self.url, {
            'check_in': today_j.strftime('%Y/%m/%d'),
            'check_out': tomorrow_j.strftime('%Y/%m/%d')
        })

        room_list = response.context['room_list']
        room_titles = [room.title for room in room_list]
        self.assertNotIn("اتاق یک تخته", room_titles)
        self.assertEqual(len(room_list), 5)

    def test_multiple_filters_combined(self):
        response = self.client.get(self.url, {
            'people': '2',
            'min_price': '700000',
            'max_price': '900000'
        })
        all_rooms = Room.objects.filter(capacity=2, price__gte=700000, price__lte=900000)
        expected_count = all_rooms.count()

        room_list = response.context['room_list']
        self.assertEqual(len(room_list), min(expected_count, 5))
        for room in room_list:
            self.assertEqual(room.capacity, 2)
            self.assertGreaterEqual(room.price, 700000)
            self.assertLessEqual(room.price, 900000)

    def test_invalid_date_format(self):
        response = self.client.get(self.url, {
            'check_in': 'invalid-date',
            'check_out': '2024/13/40'
        })
        self.assertEqual(response.status_code, 200)
        room_list = response.context['room_list']
        self.assertEqual(len(room_list), 5)

    def test_search_form_with_get_data(self):
        response = self.client.get(self.url, {'search': 'لوکس'})
        search_form = response.context['search_form']
        self.assertEqual(search_form.data.get('search'), 'لوکس')

    def test_page_navigation(self):
        response = self.client.get(self.url, {'page': '2'})
        self.assertEqual(response.status_code, 200)
        room_list = response.context['room_list']
        self.assertEqual(len(room_list), 4)

        response = self.client.get(self.url, {'page': '999'})
        self.assertEqual(response.status_code, 200)

    def test_overlapping_bookings_exclusion(self):
        check_in = date.today() + timedelta(days=5)
        check_out = date.today() + timedelta(days=10)

        Booking.objects.create(
            user=self.user,
            room=self.room2,
            check_in=check_in,
            check_out=check_out,
            people_count=2,
            status='confirmed',
            total_price=4000000,
            nights_stay=5
        )

        Booking.objects.create(
            user=self.user,
            room=self.room3,
            check_in=check_in - timedelta(days=2),
            check_out=check_in + timedelta(days=2),
            people_count=3,
            status='pending',
            total_price=3000000,
            nights_stay=4
        )

        check_in_j = jdatetime.date.fromgregorian(date=check_in + timedelta(days=1))
        check_out_j = jdatetime.date.fromgregorian(date=check_in + timedelta(days=3))

        response = self.client.get(self.url, {
            'check_in': check_in_j.strftime('%Y/%m/%d'),
            'check_out': check_out_j.strftime('%Y/%m/%d')
        })

        room_list = list(response.context['room_list'])
        all_room_titles = [room.title for room in Room.objects.all()]
        page_room_titles = [room.title for room in room_list]

        self.assertNotIn("اتاق دو تخته", page_room_titles)

        all_available_rooms = Room.objects.exclude(
            bookings__status='confirmed',
            bookings__check_in__lt=check_in + timedelta(days=3),
            bookings__check_out__gt=check_in + timedelta(days=1)
        )
        self.assertIn(self.room3, all_available_rooms)


class RoomDetailViewTest(TestCase):
    def setUp(self):
        # self.client = Client()

        self.service1 = Service.objects.create(name="WiFi")
        self.service2 = Service.objects.create(name="پارکینگ")

        self.user = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.room = Room.objects.create(
            title="اتاق دو تخته لوکس",
            price=850000,
            size=30,
            capacity=2,
            description="اتاق دو تخته با تمام امکانات"
        )
        self.room.services.add(self.service1, self.service2)

        self.url = reverse('hotels:room_detail', kwargs={'slug': self.room.slug})

        self.review1 = Review.objects.create(
            room=self.room,
            user=self.user,
            rating=5,
            comment="عالی بود"
        )

        self.review2 = Review.objects.create(
            room=self.room,
            user=self.user,
            rating=4,
            comment="خوب بود"
        )

    def test_room_detail_view_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hotels/room_detail.html')

    def test_context_data(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertEqual(context['object'], self.room)
        self.assertIsInstance(context['form'], ReviewForm)
        self.assertEqual(list(context['reviews']), [self.review2, self.review1])
        self.assertEqual(context['rating'], 4.5)

    def test_rating_breakdown(self):
        response = self.client.get(self.url)
        breakdown = response.context['rating_breakdown']

        self.assertEqual(len(breakdown), 5)
        self.assertEqual(breakdown[0]['rating'], 5)
        self.assertEqual(breakdown[0]['percentage'], 50.0)
        self.assertEqual(breakdown[1]['rating'], 4)
        self.assertEqual(breakdown[1]['percentage'], 50.0)
        self.assertEqual(breakdown[2]['rating'], 3)
        self.assertEqual(breakdown[2]['percentage'], 0)

    def test_default_dates_without_params(self):
        response = self.client.get(self.url)
        context = response.context

        today = jdatetime.date.today()
        tomorrow = today + jdatetime.timedelta(days=1)

        self.assertEqual(context['check_in'], today)
        self.assertEqual(context['check_out'], tomorrow)
        self.assertEqual(context['nights'], 1)
        self.assertEqual(context['total_price'], 850000)

    def test_valid_date_params(self):
        today = jdatetime.date.today()
        check_in = today + jdatetime.timedelta(days=5)
        check_out = today + jdatetime.timedelta(days=8)

        response = self.client.get(self.url, {
            'check_in': check_in.strftime('%Y/%m/%d'),
            'check_out': check_out.strftime('%Y/%m/%d')
        })

        context = response.context
        self.assertEqual(context['check_in'], check_in)
        self.assertEqual(context['check_out'], check_out)
        self.assertEqual(context['nights'], 3)
        self.assertEqual(context['total_price'], 2550000)
        self.assertEqual(context['form_errors'], [])

    def test_past_check_in_date(self):
        today = jdatetime.date.today()
        past_date = today - jdatetime.timedelta(days=5)

        response = self.client.get(self.url, {
            'check_in': past_date.strftime('%Y/%m/%d')
        })

        context = response.context
        self.assertEqual(context['check_in'], today)
        self.assertIn("تاریخ ورود نمی‌تواند قبل از امروز باشد.", context['form_errors'])

    def test_invalid_date_format(self):
        response = self.client.get(self.url, {
            'check_in': 'invalid date',
            'check_out': '2025/13/40'
        })

        context = response.context
        self.assertIn("فرمت تاریخ ورود نامعتبر است.", context['form_errors'])
        self.assertIn("فرمت تاریخ خروج نامعتبر است.", context['form_errors'])

    def test_check_out_before_check_in(self):
        today = jdatetime.date.today()
        check_in = today + jdatetime.timedelta(days=5)
        check_out = today + jdatetime.timedelta(days=3)

        response = self.client.get(self.url, {
            'check_in': check_in.strftime('%Y/%m/%d'),
            'check_out': check_out.strftime('%Y/%m/%d')
        })

        context = response.context
        self.assertIn("تاریخ خروج باید بعد از تاریخ ورود باشد.", context['form_errors'])
        self.assertEqual(context['check_out'], check_in + jdatetime.timedelta(days=1))

    def test_guest_forms_count(self):
        response = self.client.get(self.url)
        guest_forms = response.context['guest_forms']

        self.assertEqual(len(guest_forms), self.room.capacity)
        for i, form in enumerate(guest_forms):
            self.assertIsInstance(form, GuestForm)
            self.assertEqual(form.prefix, f'guest_{i + 1}')

    def test_post_review_not_authenticated(self):
        response = self.client.post(self.url, {
            'rating': 5,
            'comment': 'عالی'
        })
        self.assertEqual(response.status_code, 302)

    def test_post_review_authenticated_valid(self):
        self.client.login(phone='09123456789', password='testpass123')

        initial_count = Review.objects.count()

        response = self.client.post(self.url, {
            'rating': 3,
            'comment': 'متوسط بود'
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertEqual(Review.objects.count(), initial_count + 1)
        self.assertEqual(data['review_count'], 3)
        self.assertIn('review_html', data)
        self.assertIn('rating_breakdown', data)

        new_review = Review.objects.latest('created_at')
        self.assertEqual(new_review.rating, 3)
        self.assertEqual(new_review.comment, 'متوسط بود')
        self.assertEqual(new_review.user, self.user)
        self.assertEqual(new_review.room, self.room)

    def test_post_review_invalid_rating(self):
        self.client.login(phone='09123456789', password='testpass123')

        response = self.client.post(self.url, {
            'rating': 6,
            'comment': 'تست'
        })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('errors', data)

    def test_post_review_missing_comment(self):
        self.client.login(phone='09123456789', password='testpass123')

        response = self.client.post(self.url, {
            'rating': 4
        })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class ReviewDeleteViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.user2 = User.objects.create_user(
            phone='09987654321',
            password='testpass456',
        )

        self.admin_user = User.objects.create_superuser(
            phone='09111111111',
            password='adminpass',
        )

        self.room = Room.objects.create(
            title="اتاق تست",
            price=500000,
            size=25,
            capacity=2,
            description="اتاق برای تست"
        )

        self.review1 = Review.objects.create(
            room=self.room,
            user=self.user1,
            rating=5,
            comment="عالی بود"
        )

        self.review2 = Review.objects.create(
            room=self.room,
            user=self.user2,
            rating=4,
            comment="خوب بود"
        )

        self.review3 = Review.objects.create(
            room=self.room,
            user=self.user1,
            rating=3,
            comment="متوسط"
        )

    def test_delete_review_not_authenticated(self):
        url = reverse('hotels:delete_review', kwargs={'pk': self.review1.pk})
        response = self.client.delete(url, content_type='application/json')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(pk=self.review1.pk).exists())

    def test_delete_own_review_success(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:delete_review', kwargs={'pk': self.review1.pk})

        initial_count = Review.objects.count()
        response = self.client.delete(url, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertEqual(data['review_count'], initial_count - 1)
        self.assertEqual(data['rating'], 3.5)
        self.assertFalse(Review.objects.filter(pk=self.review1.pk).exists())

    def test_delete_other_user_review(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:delete_review', kwargs={'pk': self.review2.pk})

        response = self.client.delete(url, content_type='application/json')

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)

        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'شما مجاز به حذف این کامنت نیستید.')
        self.assertTrue(Review.objects.filter(pk=self.review2.pk).exists())

    def test_admin_can_delete_any_review(self):
        self.client.login(phone='09111111111', password='adminpass')
        url = reverse('hotels:delete_review', kwargs={'pk': self.review2.pk})

        response = self.client.delete(url, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertFalse(Review.objects.filter(pk=self.review2.pk).exists())

    def test_rating_breakdown_after_delete(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:delete_review', kwargs={'pk': self.review3.pk})

        response = self.client.delete(url, content_type='application/json')
        data = json.loads(response.content)

        self.assertEqual(data['rating_breakdown'][0]['rating'], 5)
        self.assertEqual(data['rating_breakdown'][0]['percentage'], 50.0)
        self.assertEqual(data['rating_breakdown'][1]['rating'], 4)
        self.assertEqual(data['rating_breakdown'][1]['percentage'], 50.0)
        self.assertEqual(data['rating_breakdown'][2]['rating'], 3)
        self.assertEqual(data['rating_breakdown'][2]['percentage'], 0)

    def test_delete_nonexistent_review(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:delete_review', kwargs={'pk': 99999})

        response = self.client.delete(url, content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_only_delete_method_allowed(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:delete_review', kwargs={'pk': self.review1.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)

    def test_multiple_reviews_rating_calculation(self):
        for i in range(1, 6):
            Review.objects.create(
                room=self.room,
                user=self.user1,
                rating=i,
                comment=f"نظر {i}"
            )

        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:delete_review', kwargs={'pk': self.review1.pk})

        response = self.client.delete(url, content_type='application/json')
        data = json.loads(response.content)

        self.assertEqual(data['review_count'], 7)
        expected_rating = (4 + 3 + 1 + 2 + 3 + 4 + 5) / 7
        self.assertAlmostEqual(data['rating'], expected_rating, places=1)

    def test_success_url_redirect(self):
        self.client.login(phone='09123456789', password='testpass123')

        review = Review.objects.create(
            room=self.room,
            user=self.user1,
            rating=5,
            comment="تست redirect"
        )

        view = ReviewDeleteView()
        view.object = review

        expected_url = reverse('hotels:room_detail', kwargs={'slug': self.room.slug})
        self.assertEqual(view.get_success_url(), expected_url)


class ReviewEditViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user1 = User.objects.create_user(
            phone='09123456789',
            password='testpass123',
        )

        self.user2 = User.objects.create_user(
            phone='09987654321',
            password='testpass456',
        )

        self.admin_user = User.objects.create_superuser(
            phone='09111111111',
            password='adminpass',

        )

        self.room = Room.objects.create(
            title="اتاق تست",
            price=500000,
            size=25,
            capacity=2,
            description="اتاق برای تست"
        )

        self.review1 = Review.objects.create(
            room=self.room,
            user=self.user1,
            rating=5,
            comment="عالی بود"
        )

        self.review2 = Review.objects.create(
            room=self.room,
            user=self.user2,
            rating=4,
            comment="خوب بود"
        )

        self.review3 = Review.objects.create(
            room=self.room,
            user=self.user1,
            rating=3,
            comment="متوسط"
        )

    def test_get_review_not_authenticated(self):
        url = reverse('hotels:edit_review', kwargs={'pk': self.review1.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

    def test_get_own_review_success(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review1.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertEqual(data['review']['rating'], 5)
        self.assertEqual(data['review']['comment'], "عالی بود")

    def test_get_other_user_review_forbidden(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review2.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)

        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'شما اجازه ویرایش این نظر را ندارید.')

    def test_admin_can_get_any_review(self):
        self.client.login(phone='09111111111', password='adminpass')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review2.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertEqual(data['review']['rating'], 4)
        self.assertEqual(data['review']['comment'], "خوب بود")

    def test_get_nonexistent_review(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_post_edit_own_review_success(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review1.pk})

        response = self.client.post(url, {
            'rating': 4,
            'comment': 'ویرایش شده - خوب بود'
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertIn('review_html', data)
        self.assertEqual(data['review_count'], 3)
        n2 = "%.1f" % data['rating']
        self.assertEqual(float(n2), 3.7)

        updated_review = Review.objects.get(pk=self.review1.pk)
        self.assertEqual(updated_review.rating, 4)
        self.assertEqual(updated_review.comment, 'ویرایش شده - خوب بود')

    def test_post_edit_other_user_review_forbidden(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review2.pk})

        response = self.client.post(url, {
            'rating': 2,
            'comment': 'تلاش برای ویرایش'
        })

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)

        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'شما اجازه ویرایش این نظر را ندارید.')

        unchanged_review = Review.objects.get(pk=self.review2.pk)
        self.assertEqual(unchanged_review.rating, 4)
        self.assertEqual(unchanged_review.comment, "خوب بود")

    def test_admin_can_edit_any_review(self):
        self.client.login(phone='09111111111', password='adminpass')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review2.pk})

        response = self.client.post(url, {
            'rating': 5,
            'comment': 'ویرایش توسط ادمین'
        })

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data['success'])

        updated_review = Review.objects.get(pk=self.review2.pk)
        self.assertEqual(updated_review.rating, 5)
        self.assertEqual(updated_review.comment, 'ویرایش توسط ادمین')

    def test_post_invalid_rating(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review1.pk})

        response = self.client.post(url, {
            'rating': 6,
            'comment': 'امتیاز نامعتبر'
        })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)

        self.assertFalse(data['success'])
        self.assertIn('errors', data)

    def test_post_missing_comment(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review1.pk})

        response = self.client.post(url, {
            'rating': 3
        })

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)

        self.assertFalse(data['success'])
        self.assertIn('errors', data)

    def test_post_nonexistent_review(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': 99999})

        response = self.client.post(url, {
            'rating': 4,
            'comment': 'تست'
        })

        self.assertEqual(response.status_code, 404)

    def test_rating_breakdown_update(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review1.pk})

        response = self.client.post(url, {
            'rating': 1,
            'comment': 'تغییر به بدترین امتیاز'
        })

        data = json.loads(response.content)

        self.assertTrue(data['success'])
        self.assertEqual(data['rating_breakdown'][0]['rating'], 5)
        self.assertEqual(data['rating_breakdown'][0]['percentage'], 0)
        self.assertEqual(data['rating_breakdown'][4]['rating'], 1)
        self.assertGreater(data['rating_breakdown'][4]['percentage'], 0)

    def test_multiple_edits_same_review(self):
        self.client.login(phone='09123456789', password='testpass123')
        url = reverse('hotels:edit_review', kwargs={'pk': self.review1.pk})

        response1 = self.client.post(url, {
            'rating': 2,
            'comment': 'ویرایش اول'
        })
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.post(url, {
            'rating': 4,
            'comment': 'ویرایش دوم'
        })
        self.assertEqual(response2.status_code, 200)

        final_review = Review.objects.get(pk=self.review1.pk)
        self.assertEqual(final_review.rating, 4)
        self.assertEqual(final_review.comment, 'ویرایش دوم')
