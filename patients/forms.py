# patients/forms.py
from django import forms
from .models import Patient
from accounts.models import Facility # Adjust this import path if Facility is in a different app
import re # For phone number validation

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'full_name', 'date_of_birth', 'current_address', 'phone_number',
            'email', 'emergency_contact_number', 'gender', 'nationality',
            'marital_status', 'occupation', 'current_status', 'current_hospital',
            'blood_group', 'genotype', 'image'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            # Add other widgets as needed for better input types/styling
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter 'current_hospital' choices to only include approved hospitals
        # This assumes 'current_hospital' is a ForeignKey to the Facility model.
        if 'current_hospital' in self.fields:
            # --- MODIFICATION START ---
            # Removed: , facility_type__iexact='hospital'
            self.fields['current_hospital'].queryset = Facility.objects.filter(
                is_approved='Approved'
            )
            # --- MODIFICATION END ---

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Enforce Rwandan format starting with +2507 followed by 8 or 9, then 7 digits
        # Updated regex to include 072, 073, 070, 071 based on common Rwandan numbers.
        if phone_number: # Only validate if a phone number is provided
            if not re.fullmatch(r'^\+2507[892301][0-9]{7}$', phone_number):
                raise forms.ValidationError("Phone number must be in Rwandan format (e.g., +25078xxxxxxx or +25079xxxxxxx).")

            # Check for uniqueness, excluding the current instance if it exists (for edits)
            qs = Patient.objects.filter(phone_number=phone_number)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This phone number is already in use by another patient.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email: # Only validate if an email is provided
            # Check for uniqueness, excluding the current instance if it exists (for edits)
            qs = Patient.objects.filter(email=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This email address is already in use by another patient.")
        return email

    def clean_emergency_contact_number(self):
        emergency_contact_number = self.cleaned_data.get('emergency_contact_number')
        if emergency_contact_number: # Only validate if an emergency contact number is provided
            # Enforce Rwandan format starting with +2507 followed by 8 or 9, then 7 digits
            # Updated regex to include 072, 073, 070, 071 based on common Rwandan numbers.
            if not re.fullmatch(r'^\+2507[892301][0-9]{7}$', emergency_contact_number):
                raise forms.ValidationError("Emergency contact number must be in Rwandan format (e.g., +25078xxxxxxx or +25079xxxxxxx).")
        return emergency_contact_number

    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
        emergency_contact_number = cleaned_data.get('emergency_contact_number')

        # Check that phone_number and emergency_contact_number do not match
        if phone_number and emergency_contact_number and phone_number == emergency_contact_number:
            self.add_error('emergency_contact_number', "Emergency contact number cannot be the same as the patient's phone number.")

        return cleaned_data