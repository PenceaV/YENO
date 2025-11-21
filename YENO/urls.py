from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from sondaje.views import login_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_redirect, name='home'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('sondaje/', include('sondaje.urls')),
    path('conturi/', include('django.contrib.auth.urls')),
]
