# Generated migration to populate cod_unic for existing teams

from django.db import migrations
import random

def genereaza_coduri(apps, schema_editor):
    Echipa = apps.get_model('sondaje', 'Echipa')
    
    for echipa in Echipa.objects.filter(cod_unic__isnull=True):
        # Generează un cod unic de 6 cifre
        while True:
            cod = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            if not Echipa.objects.filter(cod_unic=cod).exists():
                echipa.cod_unic = cod
                echipa.save()
                break

def reverse_func(apps, schema_editor):
    # Nu facem nimic la reverse
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('sondaje', '0005_echipa_cod_unic_cererealaturare'),
    ]

    operations = [
        migrations.RunPython(genereaza_coduri, reverse_func),
    ]

