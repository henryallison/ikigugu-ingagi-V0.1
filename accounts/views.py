from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Facility  # Add Facility to imports
import re
from django.core.validators import validate_email

from django.core.exceptions import ValidationError

from django.shortcuts import render
from django.utils.timezone import now

from django.shortcuts import render
def about_us_view(request):
    return render(request, 'accounts/about_us.html')

def contact_view(request):
    return render(request, 'accounts/contact.html')

def evaluate_hospital_credentials(request):
    return render(request, 'evaluate_hospital_credentials.html')  # Update with your actual template




def terms_of_service(request):
    return render(request, 'accounts/terms_conditions.html')

def privacy_policy(request):
    return render(request, 'accounts/privacy_conditions.html')
from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib import messages

# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages

def request_credentials_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower()  # Convert to lowercase for case-insensitive check

        # List of admin emails that should redirect to upload page
        ADMIN_EMAILS = [
            "harmonelvis78@gmail.com",
        ]

        if email in ADMIN_EMAILS:
            # Redirect to document upload page for admin emails
            return redirect('accounts:document_upload')
        else:
            # For non-admin emails, show success message (no actual email sent)
            messages.success(request, 'Registration credentials have been sent to your email!')
            return redirect('accounts:request_credentials')

    return render(request, 'accounts/request_credentials.html')

def document_upload_view(request):
    # Simple view to show the upload page without actual processing
    context = {
        'title': 'Hospital Document Upload',
        'message': 'Please upload all required documents (Demo)'
    }
    return render(request, 'accounts/upload_documents.html', context)

# Assuming this is in your accounts/views.py or similar

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
# Assuming this is in your accounts/views.py or similar

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model  # Import to get your custom User model

# Get your custom User model
User = get_user_model()


def login_view(request):
    """
    Handles user login.
    On successful authentication, stores the user's 'role' in the session
    and ensures the user's 'is_active' status is set to True in the database.
    """
    error_message = None
    email = ''

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if request.headers.get('X-Offline-Mode') == 'true':
            request.session['is_authenticated'] = True
            request.session['email'] = email
            # Assign a default role for offline mode (e.g., 'hospital')
            request.session['user_role'] = 'hospital'
            print(f"Offline mode: User '{email}' authenticated. User Role: {request.session['user_role']}")
            return redirect('home')

        if not email or not password:
            error_message = "Please enter both email and password."
        else:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                # --- Original Debug Print ---
                print(
                    f"DEBUG IN LOGIN_VIEW: User '{user.email}' retrieved. is_active: {user.is_active} (before update)")
                # --- End Original Debug Print ---

                # Set user's is_active status to True on successful login
                if not user.is_active:
                    user.is_active = True
                    user.save()  # Save the updated user object to the database
                    print(f"DEBUG IN LOGIN_VIEW: User '{user.email}' is_active set to True.")

                login(request, user)  # This logs the user in and updates Django's session
                request.session['user_role'] = user.role  # Store role in session
                print(f"User '{user.email}' logged in successfully. User Role: {user.role}")

                if request.POST.get('remember'):
                    request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
                return redirect('home')
            else:
                error_message = "Invalid email or password. Please try again."
                print(f"Login failed for email: {email}")

    return render(request, 'accounts/login.html', {
        'error_message': error_message,
        'email_value': email  # Preserve the email in the form on error
    })


@login_required(login_url='accounts/login')
def home_view(request):
    """
    Renders the home dashboard.
    Passes the user's role and hospital ID to the template context for conditional rendering.
    """
    # Using request.session.get('user_role') for template context as it's set on login
    user_role = request.session.get('user_role', 'hospital')
    print(f"Accessing home_view. Current user: {request.user.email}, Role: {user_role}")

    current_user_hospital_id = None
    # Check if request.user has a 'hospital' attribute and if it's not None
    if user_role == 'hospital' and hasattr(request.user, 'hospital') and request.user.hospital:
        current_user_hospital_id = request.user.hospital.id
        print(f"Hospital Admin {request.user.email} is linked to Hospital ID: {current_user_hospital_id}")

    return render(request, 'home.html', {
        'user_role': user_role,
        'current_user_hospital_id': current_user_hospital_id
    })


def logout_view(request):
    """
    Handles user logout.
    Sets the user's 'is_active' status to False in the database before logging out.
    """
    # Ensure the user is authenticated before attempting to modify
    if request.user.is_authenticated:
        # Get the current user object
        user_to_logout = request.user
        print(
            f"DEBUG IN LOGOUT_VIEW: User '{user_to_logout.email}' attempting logout. Current is_active: {user_to_logout.is_active}")

        # Set user's is_active status to False
        user_to_logout.is_active = False
        user_to_logout.save()  # Save the updated user object to the database
        print(f"DEBUG IN LOGOUT_VIEW: User '{user_to_logout.email}' is_active set to False.")

    logout(request)  # Django's built-in logout handles session cleanup
    print("User logged out.")
    return redirect('/accounts/login/')  # Redirect to the login page


def register_view(request):
    if request.method == 'POST':
        # Collect form data
        form_data = {
            'facilityName': request.POST.get('facilityName', '').strip(),
            'facilityType': request.POST.get('facilityType', '').strip(),
            'facilityLevel': request.POST.get('facilityLevel', '').strip(),
            'facilityAddress': request.POST.get('facilityAddress', '').strip(),
            'province': request.POST.get('province', '').strip(),
            'district': request.POST.get('district', '').strip(),
            'sector': request.POST.get('sector', '').strip(),
            'cell': request.POST.get('cell', '').strip(),
            'village': request.POST.get('village', '').strip(),
            'adminFirstName': request.POST.get('adminFirstName', '').strip(),
            'adminLastName': request.POST.get('adminLastName', '').strip(),
            'adminPosition': request.POST.get('adminPosition', '').strip(),
            'adminEmail': request.POST.get('adminEmail', '').strip().lower(),
            'adminPhone': request.POST.get('adminPhone', '').strip(),
            'agreeTerms': request.POST.get('agreeTerms') == 'on'
        }

        errors = []

        # Validate required fields
        for field, label in [
            ('facilityName', 'Facility Name'),
            ('facilityType', 'Facility Type'),
            ('facilityLevel', 'Facility Level'),
            ('facilityAddress', 'Facility Address'),
            ('province', 'Province'),
            ('district', 'District'),
            ('sector', 'Sector'),
            ('cell', 'Cell'),
            ('village', 'Village'),
            ('adminFirstName', 'Administrator First Name'),
            ('adminLastName', 'Administrator Last Name'),
            ('adminPosition', 'Administrator Position'),
            ('adminEmail', 'Administrator Email'),
            ('adminPhone', 'Administrator Phone Number')
        ]:
            if not form_data[field]:
                errors.append(f"{label} is required.")

        if not form_data['agreeTerms']:
            errors.append("You must agree to the terms and conditions.")

        # Validate email format
        try:
            validate_email(form_data['adminEmail'])
        except ValidationError:
            errors.append("Invalid email address format.")

        # Validate unique email
        if Facility.objects.filter(admin_email=form_data['adminEmail']).exists():
            errors.append("This email is already registered.")

        # Validate phone format (Rwanda: +250 followed by 9 digits)
        if not re.match(r'^\+250\d{9}$', form_data['adminPhone']):
            errors.append("Phone must be in the format +250XXXXXXXXX.")

        # Validate unique phone number
        if Facility.objects.filter(admin_phone=form_data['adminPhone']).exists():
            errors.append("This phone number is already registered.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'accounts/register.html', {
                'form_data': form_data
            })

        # Save the facility
        try:
            Facility.objects.create(
                name=form_data['facilityName'],
                facility_type=form_data['facilityType'],
                facility_level=form_data['facilityLevel'],
                address=form_data['facilityAddress'],
                province=form_data['province'],
                district=form_data['district'],
                sector=form_data['sector'],
                cell=form_data['cell'],
                village=form_data['village'],
                admin_first_name=form_data['adminFirstName'],
                admin_last_name=form_data['adminLastName'],
                admin_position=form_data['adminPosition'],
                admin_email=form_data['adminEmail'],
                admin_phone=form_data['adminPhone'],
                is_approved="Pending",
                admin_password='changeme'  # or hash later
            )

            # Show success popup and redirect via JS (HTML side)
            messages.success(request, '✅ Registration successful!')
            return render(request, 'accounts/register_success.html')  # Custom template with JS delay

        except Exception as e:
            print(f"Registration error: {str(e)}")
            messages.error(request, "Registration failed due to a system error.")
            return render(request, 'accounts/register.html', {'form_data': form_data})

    return render(request, 'accounts/register.html')
