from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from accounts.models import Facility
import json


# Add this entire class definition to your models.py file
class Doctor(models.Model):
    # Basic Information
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        blank=True
    )
    nationality = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(unique=True)

    # Professional Information
    specialty = models.CharField(max_length=100)
    hospital = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctors'
    )
    license_number = models.CharField(max_length=50, unique=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name
class FacilityDocument(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=100, default='Combined ZIP')
    cloudinary_url = models.URLField()
    cloudinary_public_id = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_zip_archive = models.BooleanField(default=False) # Add this line

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Facility Document'
        verbose_name_plural = 'Facility Documents'

    def __str__(self):
        return f"Documents for {self.facility.name}"

class HospitalInventory(models.Model):
    hospital = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='inventories'
    )
    inventory_list = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hospital Inventory'
        verbose_name_plural = 'Hospital Inventories'
        unique_together = ('hospital',)

    def __str__(self):
        return f"Inventory for {self.hospital.name}"

class CredentialsRequest(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='credentials_requests')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=[
        ('sent', 'Sent'),
        ('failed', 'Failed')
    ])
    # Replaced JSONField with TextField and added methods for JSON handling
    response_text = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Credentials Request'
        verbose_name_plural = 'Credentials Requests'

    @property
    def response(self):
        if self.response_text:
            return json.loads(self.response_text)
        return None

    @response.setter
    def response(self, value):
        self.response_text = json.dumps(value) if value else None

class User(AbstractUser):
    # Remove the password field from AbstractUser
    password = None
    
    # Add our own password field
    plain_password = models.CharField(max_length=128)
    
    # Add other fields
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    role = models.CharField(max_length=20)
    license_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Override the groups and user_permissions fields to use unique related_names
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='manage_hospital_user_set',
        related_query_name='user'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='manage_hospital_user_permissions_set',
        related_query_name='user'
    )
    
    def set_password(self, raw_password):
        """Set the plain text password"""
        self.plain_password = raw_password
        self.save()
    
    def set_plain_password(self, raw_password):
        """Set the plain text password"""
        self.plain_password = raw_password
        self.save()
    
    def check_password(self, raw_password):
        """Check if the provided password matches"""
        return self.plain_password == raw_password


    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
