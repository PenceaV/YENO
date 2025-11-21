from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from .models import Echipa, Intrebare, Optiune

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input'})
        self.fields['email'].widget.attrs.update({'class': 'form-input'})
        self.fields['password1'].widget.attrs.update({'class': 'form-input'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input'})

class EchipaForm(forms.ModelForm):
    class Meta:
        model = Echipa
        fields = ['nume', 'descriere']
        widgets = {
            'nume': forms.TextInput(attrs={'class': 'form-input'}),
            'descriere': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }

class SondajForm(forms.ModelForm):
    timp_limita_minute = forms.IntegerField(
        required=False,
        min_value=1,
        label='Timp limită (minute)',
        help_text='Lăsați gol pentru fără limită de timp',
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all',
            'placeholder': 'Ex: 5, 10, 30, 60...',
            'min': '1'
        })
    )
    
    class Meta:
        model = Intrebare
        fields = ['text_intrebare', 'echipa', 'tip_vot', 'is_public', 'timp_limita_minute']
        widgets = {
            'text_intrebare': forms.TextInput(attrs={'class': 'form-input'}),
            'echipa': forms.Select(attrs={'class': 'form-input'}),
            'tip_vot': forms.Select(attrs={'class': 'form-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:

            self.fields['echipa'].queryset = Echipa.objects.filter(
                models.Q(creator=user) | models.Q(membri=user)
            ).distinct()
            self.fields['echipa'].required = False
            self.fields['echipa'].empty_label = "Selectează o echipă (opțional)"

class OptiuneForm(forms.ModelForm):
    class Meta:
        model = Optiune
        fields = ['text_optiune']
        widgets = {
            'text_optiune': forms.TextInput(attrs={'class': 'form-input'}),
        }

OptiuneFormSet = forms.formset_factory(OptiuneForm, extra=2, min_num=2)

