from django import forms
from .models import Doctor, Hospital

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'hospital': forms.Select(attrs={'class': 'form-control'}),
        }