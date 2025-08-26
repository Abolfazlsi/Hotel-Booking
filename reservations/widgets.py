from django import forms
from jalali_date.widgets import AdminJalaliDateWidget
import jdatetime
from datetime import date


class CustomJalaliDateWidget(AdminJalaliDateWidget):
    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        if value:
            try:
                # فرض می‌کنیم ورودی به‌صورت شمسی (مثل 1404/05/12) است
                jalali_date = jdatetime.date.fromisoformat(value.replace('/', '-'))
                gregorian_date = jalali_date.togregorian()
                return gregorian_date
            except (ValueError, TypeError):
                return value
        return value
