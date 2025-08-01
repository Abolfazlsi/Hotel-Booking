from django import template
import jdatetime


register = template.Library()


@register.filter
def intcomma(value):
    try:
        value = float(value)
        return "{:,.0f}".format(value)
    except:
        return value


@register.filter
def number_to_persian_word(value):
    """
    تبدیل اعداد به حروف
    """
    try:
        num = int(value)
        persian_numbers = {
            1: 'اول',
            2: 'دوم',
            3: 'سوم',
            4: 'چهارم',
            5: 'پنجم',
            6: 'ششم',
            7: 'هفتم',
            8: 'هشتم',
            9: 'نهم',
            10: 'دهم',
            11: 'یازدهم',
            12: 'دوازدهم',
            13: 'سیزدهم',
            14: 'چهاردهم',
            15: 'پانزدهم',

        }
        # اگر عدد در dictb تبود عدد خام برمیگرداند
        return persian_numbers.get(num, str(num))
    except (ValueError, TypeError):
        # در صورت خطا خود عدد برگردانده میشود
        return str(value)


@register.filter
def to_jalali(value):
    if value:
        try:
            jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
            return jalali_date.strftime('%Y/%m/%d %H:%M:%S')
        except (ValueError, TypeError):
            return ''
    return ''
