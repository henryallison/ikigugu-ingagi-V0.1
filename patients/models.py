from django.db import models
from django.core.validators import RegexValidator, EmailValidator
from cloudinary.models import CloudinaryField
from accounts.models import Facility # Import the Facility model

class Patient(models.Model):
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    current_address = models.CharField(max_length=255)

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            RegexValidator(
                r'^\+2507[89]\d{7}$',
                message="Phone number must be a Rwandan number starting with '+25078' or '+25079' followed by 7 digits (e.g., +250781234567)."
            )
        ]
    )

    # --- MODIFIED: Email to be Required with a Default ---
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address.")],
        default='no-email@example.com' # Added default value
    )

    emergency_contact_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                r'^\+2507[89]\d{7}$',
                message="Emergency contact number must be a Rwandan number starting with '+25078' or '+25079' followed by 7 digits (e.g., +250781234567)."
            )
        ],
    )
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    nationality = models.CharField(max_length=50)
    marital_status = models.CharField(max_length=20, choices=[('Single', 'Single'), ('Married', 'Married'), ('Divorced', 'Divorced'), ('Widowed', 'Widowed')])

    # --- MODIFIED: Occupation to be Required with a Default ---
    occupation = models.CharField(max_length=100, default='N/A') # Added default value

    current_status = models.CharField(max_length=20, choices=[('Admitted', 'Admitted'), ('Discharged', 'Discharged'), ('In-transit', 'In-transit'), ('Outpatient', 'Outpatient')])

    current_hospital = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    blood_group = models.CharField(max_length=3, choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')])
    genotype = models.CharField(max_length=2, choices=[('AA', 'AA'), ('AS', 'AS'), ('SS', 'SS'), ('AC', 'AC')])

    # --- MODIFIED: Image Field to be Required with a Default Placeholder URL ---
    # IMPORTANT: Replace 'YOUR_CLOUD_NAME' and 'placeholder_image.png' with your actual Cloudinary details.
    # You need to upload a generic placeholder image to your Cloudinary account first.
    image = CloudinaryField(
        'image',
        default='https://res.cloudinary.com/YOUR_CLOUD_NAME/image/upload/v1/placeholder_image.png' # Added default value
    )
    cloudinary_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.full_name


class MedicalRecord(models.Model):
    """Model to store and manage patient medical records."""
    
    patient = models.ForeignKey(
        'Patient',
        on_delete=models.CASCADE,
        related_name='medical_records',
        verbose_name='Patient Name'
    )
    
    current_hospital = models.ForeignKey(
        'accounts.Facility',
        on_delete=models.CASCADE,
        related_name='medical_records',
        verbose_name='Current Hospital',
        limit_choices_to={'is_approved': True}
    )
    
    primary_diagnosis = models.TextField(
        verbose_name='Primary Diagnosis',
        help_text='Main illness or diagnosis'
    )
    
    chronic_condition = models.TextField(
        verbose_name='Chronic Condition',
        help_text='Any long-term illnesses (e.g., diabetes, asthma)',
        blank=True
    )
    
    allergies = models.TextField(
        verbose_name='Allergies',
        help_text='Known allergies (e.g., penicillin, nuts)',
        blank=True
    )
    
    past_surgeries = models.TextField(
        verbose_name='Past Surgeries',
        help_text='Prior surgeries',
        blank=True
    )
    
    current_medication = models.TextField(
        verbose_name='Current Medication',
        help_text='Current medications',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['patient'],
                name='unique_patient_record'
            )
        ]
    
    def __str__(self):
        return f"Medical Record for {self.patient.full_name}"