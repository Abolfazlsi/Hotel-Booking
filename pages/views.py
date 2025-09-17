from django.shortcuts import render
from django.views.generic import View, TemplateView, CreateView
from pages.models import ContactUs
from pages.forms import ContactForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse


class ContactUsView(LoginRequiredMixin, CreateView):
    model = ContactUs
    form_class = ContactForm
    template_name = "pages/contact_us.html"
    success_url = reverse_lazy("pages:contact_us")

    def form_valid(self, form):
        instance = form.save(commit=False)

        if self.request.user.is_authenticated:
            instance.user = self.request.user
        instance.save()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'پیام شما با موفقیت ارسال شد.'})

        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

        return super().form_invalid(form)
