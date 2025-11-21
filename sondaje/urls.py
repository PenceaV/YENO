from django.urls import path
from . import views

app_name = 'sondaje'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('guest/', views.continue_as_guest, name='guest'),
    path('echipe/', views.echipe, name='echipe'),
    path('echipe/creeaza/', views.creeaza_echipa, name='creeaza_echipa'),
    path('echipe/alaturare/', views.alaturare_echipa, name='alaturare_echipa'),
    path('echipe/join/<str:cod>/', views.join_echipa_by_code, name='join_echipa_by_code'),
    path('echipe/<int:echipa_id>/', views.detalii_echipa, name='detalii_echipa'),
    path('echipe/<int:echipa_id>/cereri/', views.gestioneaza_cereri, name='gestioneaza_cereri'),
    path('creeaza-sondaj/', views.creeaza_sondaj, name='creeaza_sondaj'),
    path('<int:intrebare_id>/', views.detalii, name='detalii'),
    path('voteaza/<int:intrebare_id>/', views.voteaza, name='voteaza'),
    path('rezultate/<int:intrebare_id>/', views.rezultate, name='rezultate'),
    path('sondajele-mele/', views.sondajele_mele, name='sondajele_mele'),
    path('sterge-sondaj/<int:intrebare_id>/', views.sterge_sondaj, name='sterge_sondaj'),
]