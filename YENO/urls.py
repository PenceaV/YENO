
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from sondaje import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_view, name='landing'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('sondaje/', include('sondaje.urls')),
    path('conturi/', include('django.contrib.auth.urls')),
]
