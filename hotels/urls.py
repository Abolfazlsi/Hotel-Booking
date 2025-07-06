from django.urls import path
from hotels import views

app_name = "hotels"

urlpatterns = [
    path("", views.HomePage.as_view(), name="home"),
    path("rooms-list/", views.RoomsListView.as_view(), name="rooms_list"),

]
