# Generated by Django 5.2.3 on 2025-07-30 06:29

import django.db.models.deletion
import django_jalali.db.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotels', '0015_alter_review_options_alter_room_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in', django_jalali.db.models.jDateField()),
                ('check_out', django_jalali.db.models.jDateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='hotels.room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
