from django.contrib import admin
from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('signup',views.signup,name="signup"),
    path('signin',views.signin,name="signin"),
    path('signout',views.signout,name="signout"),
    path('activate/<uidb64>/<token>',views.activate,name="activate"),
    path('dashboard',views.upload_timetable,name="dashboard"),
    path('dashboard2',views.upload_acdcalendar,name="dashboard2"),
    path('insights',views.userprofile,name="insights"),
]
