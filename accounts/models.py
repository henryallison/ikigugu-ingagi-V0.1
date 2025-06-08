from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_plain_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        # Superusers are typically system admins, so hospital_id should be null
        extra_fields.setdefault('hospital', None)
        return self.create_user(email, first_name, last_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('hospital', 'Hospital Administrator'),  # Updated label
        ('admin', 'System Administrator'),  # Updated label
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    password = None
    plain_password = models.CharField(max_length=128, null=True, blank=True)

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='admin')
    license_number = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.CharField(max_length=45, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    remember_token = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)

    is_staff = models.BooleanField(default=False)

    # New ForeignKey to Facility
    # Set on_delete to models.SET_NULL to allow null if a hospital is deleted
    # related_name to allow reverse access from Facility to Users
    hospital = models.ForeignKey('Facility', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='administrators')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def set_plain_password(self, raw_password):
        """Set the plain text password"""
        self.plain_password = raw_password
        self.save()

    def check_password(self, raw_password):
        """Check if the provided password matches"""
        return self.plain_password == raw_password

    def __str__(self):
        return self.email


# Keep Facility model as is, no changes needed for this specific request
from django.db import models


class Facility(models.Model):
    FACILITY_TYPE_CHOICES = (
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('urgent_care', 'Urgent Care Center'),
        ('long_term_care', 'Long-Term Care Facility'),
        ('specialty_center', 'Specialty Center'),
    )

    FACILITY_LEVEL_CHOICES = (
        ('primary', 'Primary Care'),
        ('secondary', 'Secondary Care'),
        ('tertiary', 'Tertiary Care'),
        ('quaternary', 'Quaternary Care'),
        ('emergency', 'Emergency Care'),
    )

    PROVINCE_CHOICES = (
        ('kigali', 'Kigali City'),
        ('northern', 'Northern Province'),
        ('southern', 'Southern Province'),
        ('eastern', 'Eastern Province'),
        ('western', 'Western Province'),
    )

    # Facility Information
    name = models.CharField(max_length=255)
    facility_type = models.CharField(max_length=50, choices=FACILITY_TYPE_CHOICES)
    facility_level = models.CharField(max_length=50, choices=FACILITY_LEVEL_CHOICES)
    address = models.CharField(max_length=255)

    # Location Information
    province = models.CharField(max_length=50, choices=PROVINCE_CHOICES)
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    cell = models.CharField(max_length=100)
    village = models.CharField(max_length=100)

    # Administrator Information (stored directly)
    admin_first_name = models.CharField(max_length=100, default='Hospital')
    admin_last_name = models.CharField(max_length=100, default='Hospital')
    admin_position = models.CharField(max_length=100, default='Administrator')
    admin_email = models.EmailField(unique=True, default='admin@example.com')
    admin_phone = models.CharField(max_length=20, unique=True, default='+250700000000')
    admin_password = models.CharField(max_length=255, default='changeme')  # Ensure this gets hashed on save

    # Status and Metadata
    is_approved = models.CharField(max_length=100, default='Pending')  # Changed to 'Approved' for filtering
    license_number = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def set_admin_password(self, raw_password):
        self.admin_password = make_password(raw_password)

    def check_admin_password(self, raw_password):
        return check_password(raw_password, self.admin_password)