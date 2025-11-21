from datetime import timedelta
import random

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Echipa(models.Model):
    nume = models.CharField(max_length=100)
    descriere = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='echipe_create')
    membri = models.ManyToManyField(User, related_name='echipe', blank=True)
    data_creare = models.DateTimeField('data crearii', default=timezone.now)
    cod_unic = models.CharField(max_length=6, unique=True, editable=False, verbose_name='Cod unic', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Echipe"

    def __str__(self):
        return self.nume
    
    def este_membru(self, user):
        return user == self.creator or user in self.membri.all()
    
    def genereaza_cod_unic(self):
        while True:
            cod = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            if not Echipa.objects.filter(cod_unic=cod).exists():
                return cod
    
    def save(self, *args, **kwargs):
        if not self.cod_unic:
            self.cod_unic = self.genereaza_cod_unic()
        super().save(*args, **kwargs)

class CerereAlaturare(models.Model):
    STATUS_CHOICES = [
        ('pending', 'În așteptare'),
        ('approved', 'Aprobată'),
        ('rejected', 'Respinsă'),
    ]
    
    echipa = models.ForeignKey(Echipa, on_delete=models.CASCADE, related_name='cereri_alaturare')
    utilizator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cereri_alaturare')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    data_cerere = models.DateTimeField('data cererii', default=timezone.now)
    data_raspuns = models.DateTimeField('data răspunsului', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Cereri de alăturare"
        unique_together = [('echipa', 'utilizator')]
        ordering = ['-data_cerere']

    def __str__(self):
        return f"Cerere de la {self.utilizator.username} pentru {self.echipa.nume}"

class Intrebare(models.Model):
    TIP_VOT_CHOICES = [
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
    ]
    
    text_intrebare = models.CharField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sondaje_create', null=True, blank=True)
    echipa = models.ForeignKey(Echipa, on_delete=models.CASCADE, null=True, blank=True, related_name='sondaje')
    tip_vot = models.CharField(max_length=10, choices=TIP_VOT_CHOICES, default='single')
    data_publicare = models.DateTimeField('data publicarii', default=timezone.now)
    is_public = models.BooleanField(default=True)
    allow_free_text = models.BooleanField('Permite răspuns liber', default=False, help_text='Permite utilizatorilor să introducă răspunsuri libere în loc de opțiuni predefinite')
    timp_limita_minute = models.IntegerField('timp limita (minute)', null=True, blank=True, help_text='Lăsați gol pentru fără limită de timp')
    data_expirare = models.DateTimeField('data expirarii', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Intrebari"

    def __str__(self):
        return self.text_intrebare
    
    def este_recent(self):
        now = timezone.now()
        return now - timezone.timedelta(days=1) <= self.data_publicare <= now
    
    def este_accesibil(self, user):
        if self.is_public:
            return True
        if self.echipa and user.is_authenticated:
            return self.echipa.este_membru(user)
        return False
    
    def este_expirat(self):
        if self.data_expirare:
            return timezone.now() > self.data_expirare
        return False
    
    def save(self, *args, **kwargs):
        if self.timp_limita_minute:
            if not self.data_expirare or self.pk is None:
                self.data_expirare = self.data_publicare + timedelta(minutes=self.timp_limita_minute)
        elif not self.timp_limita_minute:
            self.data_expirare = None
        super().save(*args, **kwargs)

class Optiune(models.Model):
    intrebare = models.ForeignKey(Intrebare, on_delete=models.CASCADE) 
    text_optiune = models.CharField(max_length=200)
    voturi = models.IntegerField(default=0)
    is_free_text = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Optiuni"

    def __str__(self):
        return self.text_optiune

class Vot(models.Model):
    utilizator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    intrebare = models.ForeignKey(Intrebare, on_delete=models.CASCADE)
    optiune_aleasa = models.ForeignKey(Optiune, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    data_vot = models.DateTimeField('data votului', default=timezone.now)

    class Meta:
        unique_together = [
            ('utilizator', 'intrebare', 'optiune_aleasa'),
            ('session_key', 'intrebare', 'optiune_aleasa'),
        ]

    def __str__(self):
        user_str = self.utilizator.username if self.utilizator else f"Guest ({self.session_key[:8]})"
        return f"Vot de la {user_str} pentru intrebarea: {self.intrebare.text_intrebare}"