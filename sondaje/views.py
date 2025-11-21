from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db import models
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import AuthenticationForm
from .models import Intrebare, Optiune, Vot, Echipa, CerereAlaturare
from .forms import RegisterForm, EchipaForm, SondajForm, OptiuneFormSet

def login_redirect(request):
    if request.user.is_authenticated:
        return redirect('sondaje:index')
    else:
        return redirect('sondaje:login')

def index(request):

    if not request.user.is_authenticated and not request.session.get('is_guest', False):
        return redirect('sondaje:login')

    now = timezone.now()
    echipe_user = None
    
    if request.user.is_authenticated:

        echipe_user = Echipa.objects.filter(
            models.Q(creator=request.user) | models.Q(membri=request.user)
        ).distinct()

        tip_filtre = request.GET.getlist('tip[]')
        
        if tip_filtre:

            q_objects = models.Q()
            
            for tip in tip_filtre:
                if tip == 'public':
                    q_objects |= models.Q(is_public=True)
                elif tip.isdigit():
                    q_objects |= models.Q(echipa_id=int(tip))
            
            if q_objects:
                ultimele_intrebari = Intrebare.objects.filter(q_objects).filter(
                    models.Q(data_expirare__isnull=True) | models.Q(data_expirare__gt=now)
                ).distinct().order_by('-data_publicare')[:20]
            else:

                ultimele_intrebari = Intrebare.objects.filter(
                    models.Q(is_public=True) | models.Q(echipa__in=echipe_user)
                ).filter(
                    models.Q(data_expirare__isnull=True) | models.Q(data_expirare__gt=now)
                ).distinct().order_by('-data_publicare')[:20]
        else:

            ultimele_intrebari = Intrebare.objects.filter(
                models.Q(is_public=True) | models.Q(echipa__in=echipe_user)
            ).filter(
                models.Q(data_expirare__isnull=True) | models.Q(data_expirare__gt=now)
            ).distinct().order_by('-data_publicare')[:20]
    else:

        ultimele_intrebari = Intrebare.objects.filter(
            is_public=True
        ).filter(
            models.Q(data_expirare__isnull=True) | models.Q(data_expirare__gt=now)
        ).order_by('-data_publicare')[:20]

    filtre_active = []
    if request.user.is_authenticated:
        filtre_active = request.GET.getlist('tip[]', [])
    
    context = {
        'lista_intrebari': ultimele_intrebari,
        'echipele_user': echipe_user,
        'filtre_active': filtre_active,
    }

    return render(request, 'sondaje/index.html', context)

def detalii(request, intrebare_id):
    intrebare = get_object_or_404(Intrebare, pk=intrebare_id)

    if not intrebare.este_accesibil(request.user):
        return render(request, 'sondaje/detalii.html', {
            'intrebare': intrebare,
            'mesaj_eroare': "Nu ai acces la acest sondaj!",
        })

    if intrebare.este_expirat():
        return render(request, 'sondaje/detalii.html', {
            'intrebare': intrebare,
            'mesaj_eroare': "Acest sondaj a expirat!",
            'a_votat': True,
        })

    a_votat = False
    if request.user.is_authenticated:
        a_votat = Vot.objects.filter(utilizator=request.user, intrebare=intrebare).exists()
    else:
        session_key = request.session.session_key
        if session_key:
            a_votat = Vot.objects.filter(session_key=session_key, intrebare=intrebare).exists()

    context = {
        'intrebare': intrebare,
        'a_votat': a_votat,
    }

    return render(request, 'sondaje/detalii.html', context)

@require_http_methods(["POST"])
def voteaza(request, intrebare_id):
    intrebare = get_object_or_404(Intrebare, pk=intrebare_id)

    if intrebare.este_expirat():
        return render(request, 'sondaje/detalii.html', {
            'intrebare': intrebare,
            'mesaj_eroare': "Acest sondaj a expirat și nu mai poate primi voturi!",
            'a_votat': True,
        })

    if not intrebare.este_accesibil(request.user):
        return render(request, 'sondaje/detalii.html', {
            'intrebare': intrebare,
            'mesaj_eroare': "Nu ai acces la acest sondaj!",
        })

    if request.user.is_authenticated:
        if intrebare.tip_vot == 'single':
            if Vot.objects.filter(utilizator=request.user, intrebare=intrebare).exists():
                return render(request, 'sondaje/detalii.html', {
                    'intrebare': intrebare,
                    'mesaj_eroare': "Ai votat deja la acest sondaj!",
                })
    else:

        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        
        if intrebare.tip_vot == 'single':
            if Vot.objects.filter(session_key=session_key, intrebare=intrebare).exists():
                return render(request, 'sondaje/detalii.html', {
                    'intrebare': intrebare,
                    'mesaj_eroare': "Ai votat deja la acest sondaj!",
                })

    try:
        free_text = request.POST.get('free_text_response', '').strip()
        optiune_id = request.POST.get('optiune')
        optiuni_ids = request.POST.getlist('optiune')
        
        if intrebare.tip_vot == 'single':
            if optiune_id:
                optiune_selectata = intrebare.optiune_set.get(pk=optiune_id)
                optiune_selectata.voturi += 1
                optiune_selectata.save()
                
                Vot.objects.create(
                    utilizator=request.user if request.user.is_authenticated else None,
                    intrebare=intrebare,
                    optiune_aleasa=optiune_selectata,
                    session_key=request.session.session_key if not request.user.is_authenticated else None
                )
            elif intrebare.allow_free_text and free_text:
                optiune_selectata, created = Optiune.objects.get_or_create(
                    intrebare=intrebare,
                    text_optiune=free_text,
                    defaults={'is_free_text': True, 'voturi': 0}
                )
                
                if not created:
                    optiune_selectata.voturi += 1
                    optiune_selectata.save()
                else:
                    optiune_selectata.voturi = 1
                    optiune_selectata.save()
                
                Vot.objects.create(
                    utilizator=request.user if request.user.is_authenticated else None,
                    intrebare=intrebare,
                    optiune_aleasa=optiune_selectata,
                    session_key=request.session.session_key if not request.user.is_authenticated else None
                )
            else:
                raise KeyError
        else:
            if optiuni_ids:
                for optiune_id in optiuni_ids:
                    optiune_selectata = intrebare.optiune_set.get(pk=optiune_id)
                    optiune_selectata.voturi += 1
                    optiune_selectata.save()
                    
                    Vot.objects.create(
                        utilizator=request.user if request.user.is_authenticated else None,
                        intrebare=intrebare,
                        optiune_aleasa=optiune_selectata,
                        session_key=request.session.session_key if not request.user.is_authenticated else None
                    )
            
            if intrebare.allow_free_text and free_text:
                optiune_selectata, created = Optiune.objects.get_or_create(
                    intrebare=intrebare,
                    text_optiune=free_text,
                    defaults={'is_free_text': True, 'voturi': 0}
                )
                
                if not created:
                    optiune_selectata.voturi += 1
                    optiune_selectata.save()
                else:
                    optiune_selectata.voturi = 1
                    optiune_selectata.save()
                
                Vot.objects.create(
                    utilizator=request.user if request.user.is_authenticated else None,
                    intrebare=intrebare,
                    optiune_aleasa=optiune_selectata,
                    session_key=request.session.session_key if not request.user.is_authenticated else None
                )
            
            if not optiuni_ids and not (intrebare.allow_free_text and free_text):
                raise KeyError
    except (KeyError, Optiune.DoesNotExist):
        return render(request, 'sondaje/detalii.html', {
            'intrebare': intrebare,
            'mesaj_eroare': "Nu ai selectat o optiune valida"
        })

    return HttpResponseRedirect(reverse('sondaje:rezultate', args=(intrebare.id,)))
    
def rezultate(request, intrebare_id):
    intrebare = get_object_or_404(Intrebare, pk=intrebare_id)

    if not intrebare.este_accesibil(request.user):
        return render(request, 'sondaje/rezultate.html', {
            'intrebare': intrebare,
            'mesaj_eroare': "Nu ai acces la acest sondaj!",
        })
    
    optiuni = intrebare.optiune_set.all()
    total_voturi = sum(optiune.voturi for optiune in optiuni)
    
    context = {
        'intrebare': intrebare,
        'total_voturi': total_voturi,
    }
    return render(request, 'sondaje/rezultate.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('sondaje:index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(username=username, password=password)
            if user is not None:
                if 'is_guest' in request.session:
                    del request.session['is_guest']
                login(request, user)
                next_url = request.GET.get('next', '/sondaje/')
                return redirect(next_url)
        
        form.add_error(None, 'Utilizatorul sau parola sunt greșite.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'sondaje/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            if 'is_guest' in request.session:
                del request.session['is_guest']
            login(request, user)
            return redirect('sondaje:index')
    else:
        form = RegisterForm()
    return render(request, 'sondaje/register.html', {'form': form})

def continue_as_guest(request):
    
    if not request.session.session_key:
        request.session.create()
    request.session['is_guest'] = True
    request.session.save()
    return redirect('sondaje:index')

@login_required
def creeaza_echipa(request):
    if request.method == 'POST':
        form = EchipaForm(request.POST)
        if form.is_valid():
            echipa = form.save(commit=False)
            echipa.creator = request.user
            echipa.save()
            echipa.membri.add(request.user)
            return redirect('sondaje:echipe')
    else:
        form = EchipaForm()
    return render(request, 'sondaje/creeaza_echipa.html', {'form': form})

@login_required
def echipe(request):
    echipele = Echipa.objects.filter(
        models.Q(creator=request.user) | models.Q(membri=request.user)
    ).distinct()
    
    echipele_user = Echipa.objects.filter(
        models.Q(creator=request.user) | models.Q(membri=request.user)
    ).distinct()
    
    poate_crea_echipa = not echipele_user.exists()
    
    return render(request, 'sondaje/echipe.html', {
        'echipele': echipele,
        'poate_crea_echipa': poate_crea_echipa
    })

@login_required
def detalii_echipa(request, echipa_id):
    
    echipa = get_object_or_404(Echipa, pk=echipa_id)

    if not echipa.este_membru(request.user):
        return render(request, 'sondaje/detalii_echipa.html', {
            'echipa': echipa,
            'mesaj_eroare': 'Nu ai acces la această echipă!',
        })
    
    sondajele = Intrebare.objects.filter(echipa=echipa).order_by('-data_publicare')

    cereri = None
    if echipa.creator == request.user:
        cereri = echipa.cereri_alaturare.filter(status='pending')
    
    return render(request, 'sondaje/detalii_echipa.html', {
        'echipa': echipa,
        'sondajele': sondajele,
        'cereri': cereri,
    })

def join_echipa_by_code(request, cod):
    if not request.user.is_authenticated:
        return redirect('sondaje:login')
    
    try:
        echipa = Echipa.objects.get(cod_unic=cod)
        
        if echipa.este_membru(request.user):
            return render(request, 'sondaje/alaturare_echipa.html', {
                'mesaj': 'Ești deja membru al acestei echipe.',
                'mesaj_tip': 'info',
            })
        
        cerere_existenta = CerereAlaturare.objects.filter(
            echipa=echipa,
            utilizator=request.user,
            status='pending'
        ).first()
        
        if cerere_existenta:
            return render(request, 'sondaje/alaturare_echipa.html', {
                'mesaj': 'Ai deja o cerere în așteptare pentru această echipă.',
                'mesaj_tip': 'info',
            })
        
        CerereAlaturare.objects.create(
            echipa=echipa,
            utilizator=request.user
        )
        
        return render(request, 'sondaje/alaturare_echipa.html', {
            'mesaj': f'Cererea ta de alăturare la echipa "{echipa.nume}" a fost trimisă. Creatorul echipei va primi o notificare.',
            'mesaj_tip': 'success',
        })
    except Echipa.DoesNotExist:
        return render(request, 'sondaje/alaturare_echipa.html', {
            'mesaj': 'Codul introdus nu este valid.',
            'mesaj_tip': 'error',
        })

@login_required
def alaturare_echipa(request):
    
    mesaj = None
    mesaj_tip = None
    
    if request.method == 'POST':
        cod = request.POST.get('cod', '').strip()
        
        if len(cod) != 6 or not cod.isdigit():
            mesaj = 'Codul trebuie să fie format din exact 6 cifre.'
            mesaj_tip = 'error'
        else:
            try:
                echipa = Echipa.objects.get(cod_unic=cod)

                if echipa.este_membru(request.user):
                    mesaj = 'Ești deja membru al acestei echipe.'
                    mesaj_tip = 'info'
                else:

                    cerere_existenta = CerereAlaturare.objects.filter(
                        echipa=echipa,
                        utilizator=request.user,
                        status='pending'
                    ).first()
                    
                    if cerere_existenta:
                        mesaj = 'Ai deja o cerere în așteptare pentru această echipă.'
                        mesaj_tip = 'info'
                    else:

                        CerereAlaturare.objects.create(
                            echipa=echipa,
                            utilizator=request.user
                        )
                        mesaj = f'Cererea ta de alăturare la echipa "{echipa.nume}" a fost trimisă. Creatorul echipei va primi o notificare.'
                        mesaj_tip = 'success'
            except Echipa.DoesNotExist:
                mesaj = 'Codul introdus nu este valid. Verifică codul și încearcă din nou.'
                mesaj_tip = 'error'
    
    return render(request, 'sondaje/alaturare_echipa.html', {
        'mesaj': mesaj,
        'mesaj_tip': mesaj_tip,
    })

@login_required
def gestioneaza_cereri(request, echipa_id):
    
    echipa = get_object_or_404(Echipa, id=echipa_id)

    if echipa.creator != request.user:
        return redirect('sondaje:echipe')
    
    if request.method == 'POST':
        cerere_id = request.POST.get('cerere_id')
        actiune = request.POST.get('actiune')
        
        try:
            cerere = CerereAlaturare.objects.get(id=cerere_id, echipa=echipa, status='pending')
            
            if actiune == 'approve':
                cerere.status = 'approved'
                cerere.data_raspuns = timezone.now()
                cerere.save()
                echipa.membri.add(cerere.utilizator)
                mesaj = f'Cererea lui {cerere.utilizator.username} a fost aprobată.'
            elif actiune == 'reject':
                cerere.status = 'rejected'
                cerere.data_raspuns = timezone.now()
                cerere.save()
                mesaj = f'Cererea lui {cerere.utilizator.username} a fost respinsă.'
        except CerereAlaturare.DoesNotExist:
            mesaj = 'Cererea nu a fost găsită.'
    
    cereri_pending = echipa.cereri_alaturare.filter(status='pending').order_by('-data_cerere')
    cereri_aprobate = echipa.cereri_alaturare.filter(status='approved').order_by('-data_raspuns')[:10]
    cereri_respinse = echipa.cereri_alaturare.filter(status='rejected').order_by('-data_raspuns')[:10]
    
    return render(request, 'sondaje/gestioneaza_cereri.html', {
        'echipa': echipa,
        'cereri_pending': cereri_pending,
        'cereri_aprobate': cereri_aprobate,
        'cereri_respinse': cereri_respinse,
    })

@login_required
def creeaza_sondaj(request):
    if request.method == 'POST':
        form = SondajForm(request.POST, user=request.user)
        formset = OptiuneFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            sondaj = form.save(commit=False)
            sondaj.creator = request.user
            sondaj.is_public = not sondaj.echipa


            if sondaj.timp_limita_minute:
                from datetime import timedelta
                sondaj.data_expirare = sondaj.data_publicare + timedelta(minutes=sondaj.timp_limita_minute)
            else:
                sondaj.data_expirare = None
            
            sondaj.save()

            for optiune_form in formset:
                if optiune_form.cleaned_data.get('text_optiune'):
                    Optiune.objects.create(
                        intrebare=sondaj,
                        text_optiune=optiune_form.cleaned_data['text_optiune']
                    )
            
            return redirect('sondaje:detalii', sondaj.id)
    else:
        form = SondajForm(user=request.user)
        formset = OptiuneFormSet()
    
    return render(request, 'sondaje/creeaza_sondaj.html', {
        'form': form,
        'formset': formset,
    })

@login_required
def sondajele_mele(request):
    
    sondajele = Intrebare.objects.filter(creator=request.user).order_by('-data_publicare')
    
    return render(request, 'sondaje/sondajele_mele.html', {
        'sondajele': sondajele,
    })

@login_required
@require_http_methods(["POST"])
def sterge_sondaj(request, intrebare_id):
    
    intrebare = get_object_or_404(Intrebare, pk=intrebare_id)

    if intrebare.creator != request.user:
        return render(request, 'sondaje/sondajele_mele.html', {
            'sondajele': Intrebare.objects.filter(creator=request.user).order_by('-data_publicare'),
            'mesaj_eroare': 'Nu ai permisiunea să ștergi acest sondaj!',
        })
    
    intrebare.delete()
    return redirect('sondaje:sondajele_mele')