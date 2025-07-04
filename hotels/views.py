from django.shortcuts import render
from django.views.generic import TemplateView
from hotels.models import Room


class HomePage(TemplateView):
    template_name = "hotels/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["top_rooms"] = Room.objects.all()[:3]
        context["rooms_list"] = Room.objects.all()
        return context
