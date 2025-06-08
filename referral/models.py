# referral/models.py
from django.db import models
from django.utils import timezone
import uuid

# Import your existing models
from patients.models import Patient # This is your Patient model
from manage_hospital.models import Facility, Doctor # These are your Facility (Hospital) and Doctor models


class Referral(models.Model):
    """
    Model to store details of a patient referral between hospitals/doctors.
    """
    STATUS_CHOICES = [
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled'),
    ]

    PRIORITY_CHOICES = [
        ('Emergency', 'Emergency'),
        ('Urgent care', 'Urgent care'),
        ('Routine', 'Routine'),
    ]

    # Foreign Keys to other models, adjusted to your provided models
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='referrals_as_patient')
    referring_hospital = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='outgoing_referrals')
    referring_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='referrals_made')
    receiving_hospital = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='incoming_referrals')
    receiving_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='referrals_received')

    # Referral details from the form
    # Note: The referral_code will be generated in the view and passed,
    # or you can re-enable generation in save() if you prefer it model-side.
    referral_code = models.CharField(max_length=20, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Requested')
    main_reason = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    start_datetime = models.DateTimeField(default=timezone.now)
    end_datetime = models.DateTimeField(null=True, blank=True) # Optional
    additional_notes = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        ordering = ['-created_at'] # Order by most recent first

    def __str__(self):
        return f"Referral {self.referral_code} for {self.patient.full_name}"

    # You could add a method here to auto-generate if you remove it from the view
    # def _generate_unique_referral_code(self):
    #     while True:
    #         code = f"REF-{str(uuid.uuid4())[:8].upper()}"
    #         if not Referral.objects.filter(referral_code=code).exists():
    #             return code

    # def save(self, *args, **kwargs):
    #     if not self.pk and not self.referral_code: # Only generate on first save if not already set
    #         self.referral_code = self._generate_unique_referral_code()
    #     super().save(*args, **kwargs)