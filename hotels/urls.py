from django.urls import path, re_path
from hotels import views

app_name = "hotels"

urlpatterns = [
    # homepage
    path("", views.HomePage.as_view(), name="home"),

    # rooms
    path("rooms-list/", views.RoomsListView.as_view(), name="rooms_list"),
    re_path(r"room-detail/(?P<slug>[-\w]*)/", views.RoomDetailView.as_view(), name="room_detail"),

]
