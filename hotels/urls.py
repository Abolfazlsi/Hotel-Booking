from django.urls import path, re_path
from hotels import views

app_name = "hotels"

urlpatterns = [
    # homepage
    path("", views.HomePage.as_view(), name="home"),
    path("clear", views.clear_cache, name="clear"),


    # rooms
    path("rooms-list/", views.RoomsListView.as_view(), name="rooms_list"),
    re_path(r"room-detail/(?P<slug>[-\w]+)/", views.RoomDetailView.as_view(), name="room_detail"),

    # reviews
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='delete_review'),
    path('review/<int:pk>/edit/', views.ReviewEditView.as_view(), name='edit_review'),

]
