from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from hotels.models import Room
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.template.defaultfilters import truncatewords


class HomePage(TemplateView):
    template_name = "hotels/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["top_rooms"] = Room.objects.all()[:3]
        context["rooms_list"] = Room.objects.all()[:5]
        return context


class RoomsListView(ListView):
    model = Room
    template_name = "hotels/rooms.html"
    paginate_by = 2
    context_object_name = 'room_list'  # نام متغیر برای دسترسی به لیست اتاق‌ها در قالب

    def get(self, request, *args, **kwargs):
        rooms = Room.objects.all()
        sort = request.GET.get('sort', 'default')
        page = request.GET.get('page', 1)

        # اعمال مرتب‌سازی بر اساس پارامتر sort
        if sort == 'lower-price':
            rooms = rooms.order_by('price')
        elif sort == 'higher-price':
            rooms = rooms.order_by('-price')

        # صفحه‌بندی
        paginator = Paginator(rooms, self.paginate_by)
        try:
            room_list = paginator.page(page)
        except PageNotAnInteger:
            room_list = paginator.page(1)
        except EmptyPage:
            room_list = paginator.page(paginator.num_pages)

        # بررسی اینکه درخواست از نوع AJAX است یا خیر
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # آماده‌سازی داده‌ها برای JSON
            room_data = []
            for room in room_list:
                room_data.append({
                    'title': room.title,
                    'price': room.price,
                    'description': truncatewords(room.description, 25),
                    'image_url': room.primary_image.image.url if room.primary_image else '',
                    'alt_text': room.primary_image.alt_text if room.primary_image else '',
                    'services': [service.name for service in room.services.all()],
                    'url': room.get_absolute_url(),
                })

            return JsonResponse({
                'room_list': room_data,
                'has_previous': room_list.has_previous(),
                'has_next': room_list.has_next(),
                'previous_page_number': room_list.previous_page_number() if room_list.has_previous() else None,
                'next_page_number': room_list.next_page_number() if room_list.has_next() else None,
                'current_page': room_list.number,
                'total_pages': paginator.num_pages,
            })
        else:
            # رندر کردن قالب HTML برای درخواست‌های معمولی
            return render(request, self.template_name, {
                'room_list': room_list,
                'page_obj': room_list,  # برای صفحه‌بندی در قالب
            })


class RoomDetailView(DetailView):
    model = Room
    template_name = "hotels/room_detail.html"
