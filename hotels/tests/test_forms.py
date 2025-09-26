from django.test import TestCase
from hotels.forms import ReviewForm
from django import forms
from hotels.forms import SearchForm
from datetime import timedelta
from jalali_date import date2jalali
import jdatetime as jdate


class ReviewFormTest(TestCase):
    def test_valid_form(self):
        data = {'rating': 3, 'comment': 'This is a test comment.'}
        form = ReviewForm(data=data)
        self.assertTrue(form.is_valid())

    def test_missing_comment(self):
        data = {'rating': 3}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)

    def test_invalid_rating_below_min(self):
        data = {'rating': 0, 'comment': 'Test comment'}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        self.assertEqual(form.errors['rating'], ['امتیاز باید بین ۱ تا ۵ باشد.'])

    def test_invalid_rating_above_max(self):
        data = {'rating': 6, 'comment': 'Test comment'}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        self.assertEqual(form.errors['rating'], ['امتیاز باید بین ۱ تا ۵ باشد.'])

    def test_invalid_rating_none(self):
        data = {'comment': 'Test comment'}
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rating', form.errors)
        self.assertEqual(form.errors['rating'], ['این فیلد لازم است.'])

    def test_widgets(self):
        form = ReviewForm()
        self.assertIsInstance(form.fields['comment'].widget, forms.Textarea)
        self.assertEqual(form.fields['comment'].widget.attrs['class'], 'form-control')
        self.assertEqual(form.fields['comment'].widget.attrs['rows'], 4)
        self.assertEqual(form.fields['comment'].widget.attrs['required'], 'required')
        self.assertEqual(form.fields['comment'].widget.attrs['placeholder'], 'نظر خود را اینجا بنویسید...')
        self.assertIsInstance(form.fields['rating'].widget, forms.HiddenInput)
        self.assertEqual(form.fields['rating'].widget.attrs['id'], 'rating-value')


class SearchFormTest(TestCase):

    def test_valid_form(self):
        today = jdate.date.today()
        check_in = today.strftime('%Y-%m-%d')
        check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')
        data = {
            'check_in': check_in,
            'check_out': check_out,
            'adults': 2,
            'children': 1,
            'people_count': 3,
            'min_price': 100,
            'max_price': 500
        }
        form = SearchForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_check_out_before_check_in(self):
        today = jdate.date.today()
        check_in = (today + timedelta(days=3)).strftime('%Y-%m-%d')
        check_out = today.strftime('%Y-%m-%d')
        data = {
            'check_in': check_in,
            'check_out': check_out
        }
        form = SearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(form.errors['__all__'], ['تاریخ خروج باید بعد از تاریخ ورود باشد.'])

    def test_invalid_check_out_equal_check_in(self):
        today = jdate.date.today()
        check_in = today.strftime('%Y-%m-%d')
        check_out = today.strftime('%Y-%m-%d')
        data = {
            'check_in': check_in,
            'check_out': check_out
        }
        form = SearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(form.errors['__all__'], ['تاریخ خروج باید بعد از تاریخ ورود باشد.'])

    def test_missing_check_in(self):
        today = jdate.date.today()
        check_out = (today + timedelta(days=3)).strftime('%Y/%m/%d')
        data = {'check_out': check_out}
        form = SearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('check_in', form.errors)

    def test_missing_check_out(self):
        today = jdate.date.today()
        check_in = today.strftime('%Y/%m/%d')
        data = {'check_in': check_in}
        form = SearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('check_out', form.errors)

    def test_invalid_integer_fields(self):
        today = jdate.date.today()
        check_in = today.strftime('%Y/%m/%d')
        check_out = (today + timedelta(days=3)).strftime('%Y/%m/%d')
        data = {
            'check_in': check_in,
            'check_out': check_out,
            'adults': 'integer',
        }
        form = SearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('adults', form.errors)
