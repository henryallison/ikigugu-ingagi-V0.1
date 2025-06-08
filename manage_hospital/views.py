from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from datetime import datetime
from manage_hospital.utils.sms import send_sms
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from accounts.models import User
import logging
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re



logger = logging.getLogger(__name__)

# Make sure your Cloudinary configuration is loaded (usually done automatically by the SDK
# if CLOUDINARY_URL is set, or if CLOUDINARY_CLOUD_NAME, API_KEY, API_SECRET are in settings.py)
# If not, you might need:
# import cloudinary
# cloudinary.config(
#     cloud_name = settings.CLOUDINARY_CLOUD_NAME,
#     api_key = settings.CLOUDINARY_API_KEY,
#     api_secret = settings.CLOUDINARY_API_SECRET
# )
# In your views.py file
# ... (existing imports)
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt # CONSIDER REMOVING THIS AND USING CSRF TOKEN IN HEADERS
import json
from .models import Doctor, Facility, HospitalInventory  # Import HospitalInventory model

# ... (your existing views like manage_doctors, add_doctor, etc.)


@require_POST
@csrf_exempt
def edit_doctor_ajax(request, doctor_id):
    try:
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        data = json.loads(request.body)

        # Retrieve new values, falling back to existing values if not provided by the AJAX request
        full_name = data.get('full_name')
        date_of_birth = data.get('date_of_birth')
        gender = data.get('gender')
        nationality = data.get('nationality')
        address = data.get('address')
        phone_number = data.get('phone_number')
        email = data.get('email')
        specialty = data.get('specialty')
        hospital_id = data.get('hospital')
        license_number = data.get('license_number')

        # --- Apply "all fields are required" validation ---
        # For an AJAX update, fields not sent by the client should retain their existing value.
        # This means we should only validate if the *received* fields are not empty,
        # or if existing fields become empty if the client explicitly sends an empty string.
        # However, following the spirit of 'add_doctor', we'll ensure *all* fields are present
        # and valid, either from the request or the existing doctor object.

        # Let's ensure the current values of the doctor are used if not provided in the update data
        updated_full_name = full_name if full_name is not None else doctor.full_name
        updated_date_of_birth = date_of_birth if date_of_birth is not None else doctor.date_of_birth
        updated_gender = gender if gender is not None else doctor.gender
        updated_nationality = nationality if nationality is not None else doctor.nationality
        updated_address = address if address is not None else doctor.address
        updated_phone_number = phone_number if phone_number is not None else doctor.phone_number
        updated_email = email if email is not None else doctor.email
        updated_specialty = specialty if specialty is not None else doctor.specialty
        updated_hospital_id = hospital_id if hospital_id is not None else (doctor.hospital.pk if doctor.hospital else None)
        updated_license_number = license_number if license_number is not None else doctor.license_number

        # Basic validation: Check if essential fields, after considering updates, are not empty
        if not all([updated_full_name, updated_date_of_birth, updated_gender, updated_nationality, updated_address,
                    updated_phone_number, updated_email, updated_specialty, updated_hospital_id, updated_license_number]):
            return JsonResponse({'success': False, 'error': "All fields are required. Please fill out the form completely."}, status=400)


        # --- Validate email format ---
        # Only validate if the email has changed or if it was null and now has a value
        if updated_email and (updated_email != doctor.email):
            try:
                validate_email(updated_email)
            except ValidationError:
                return JsonResponse({'success': False, 'error': 'Invalid email format.'}, status=400)

        # --- Validate Rwandan phone number format ---
        # Only validate if the phone number has changed or if it was null and now has a value
        if updated_phone_number and (updated_phone_number != doctor.phone_number):
            if not validate_rwanda_phone(updated_phone_number):
                return JsonResponse({'success': False, 'error': "Invalid Rwandan phone number format. Examples: +25078XXXXXXX or 078XXXXXXX."}, status=400)

        # --- Check for phone number uniqueness (excluding the current doctor) ---
        if updated_phone_number and (updated_phone_number != doctor.phone_number) and \
           Doctor.objects.filter(phone_number=updated_phone_number).exclude(pk=doctor_id).exists():
            return JsonResponse({'success': False, 'error': f"A doctor with the phone number '{updated_phone_number}' already exists."}, status=409)

        # --- Check for email uniqueness (excluding the current doctor) ---
        if updated_email and (updated_email != doctor.email) and \
           Doctor.objects.filter(email=updated_email).exclude(pk=doctor_id).exists():
            return JsonResponse({'success': False, 'error': f"A doctor with the email '{updated_email}' already exists."}, status=409)

        # --- Check for license number uniqueness (excluding the current doctor) ---
        if updated_license_number and (updated_license_number != doctor.license_number) and \
           Doctor.objects.filter(license_number=updated_license_number).exclude(pk=doctor_id).exists():
            return JsonResponse({'success': False, 'error': f"A doctor with the license number '{updated_license_number}' already exists."}, status=409)

        # --- Retrieve the hospital object, ensuring its 'is_approved' status is 'Approved' ---
        hospital = None
        if updated_hospital_id:
            try:
                hospital = get_object_or_404(Facility, pk=updated_hospital_id, is_approved='Approved')
            except Facility.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Selected hospital not found or not approved.'}, status=400)
        # If updated_hospital_id is None, it means the client might want to unset the hospital, which is allowed.

        # --- Update the doctor object's fields ---
        doctor.full_name = updated_full_name
        doctor.date_of_birth = updated_date_of_birth
        doctor.gender = updated_gender
        doctor.nationality = updated_nationality
        doctor.address = updated_address
        doctor.phone_number = updated_phone_number
        doctor.email = updated_email
        doctor.specialty = updated_specialty
        doctor.license_number = updated_license_number
        doctor.hospital = hospital # Assign the validated hospital object (or None)

        doctor.save()

        return JsonResponse({
            'success': True,
            'message': 'Doctor updated successfully!',
            'doctor': {
                'id': doctor.id,
                'full_name': doctor.full_name,
                'date_of_birth': str(doctor.date_of_birth) if doctor.date_of_birth else None,
                'gender': doctor.gender,
                'nationality': doctor.nationality,
                'phone_number': doctor.phone_number,
                'address': doctor.address,
                'email': doctor.email,
                'specialty': doctor.specialty,
                'hospital_name': doctor.hospital.name if doctor.hospital else 'N/A',
                'license_number': doctor.license_number,
            }
        })
    except Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Doctor not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON in request body.'}, status=400)
    except IntegrityError as e:
        logger.error(f"Integrity error editing doctor {doctor_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': "An internal database error occurred (possible duplicate entry). Please try again."}, status=500)
    except Exception as e:
        logger.error(f"An unexpected error occurred while editing doctor {doctor_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': f"An unexpected error occurred: {str(e)}"}, status=500)

# AJAX View for Deleting a Doctor
@require_POST
@csrf_exempt
def delete_doctor_ajax(request, doctor_id):
    try:
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        doctor_name = doctor.full_name
        doctor.delete()
        return JsonResponse({'success': True, 'message': f'Doctor "{doctor_name}" deleted successfully!'})
    except Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Doctor not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting doctor {doctor_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
# In your views.py file

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Doctor, Facility

from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from datetime import datetime
from manage_hospital.utils.sms import send_sms
import json
from manage_hospital.models import Facility, CredentialsRequest, FacilityDocument
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings # Make sure settings is imported to access CLOUDINARY_ configs
from accounts.models import User # Ensure User is imported if used elsewhere in the file
import logging

logger = logging.getLogger(__name__)

# --- Doctor Management Views ---

@csrf_exempt
def manage_doctors(request):
    # Handles AJAX POST requests for editing and deleting doctors
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            doctor_id = data.get('id')

            if action == 'edit':
                # --- Start Edit Doctor Logic with All Validations ---
                try:
                    doctor = get_object_or_404(Doctor, pk=doctor_id)

                    # Retrieve new values from request data, falling back to existing values
                    # 'None' checks are crucial for fields that might not be sent in a partial update
                    full_name = data.get('full_name')
                    date_of_birth = data.get('date_of_birth')
                    gender = data.get('gender')
                    nationality = data.get('nationality')
                    phone_number = data.get('phone_number')
                    address = data.get('address')
                    email = data.get('email')
                    specialty = data.get('specialty')
                    hospital_id = data.get('hospital')
                    license_number = data.get('license_number')

                    # Determine the effective value for validation: new data if present, else current doctor's value
                    updated_full_name = full_name if full_name is not None else doctor.full_name
                    updated_date_of_birth = date_of_birth if date_of_birth is not None else doctor.date_of_birth
                    updated_gender = gender if gender is not None else doctor.gender
                    updated_nationality = nationality if nationality is not None else doctor.nationality
                    updated_address = address if address is not None else doctor.address
                    updated_phone_number = phone_number if phone_number is not None else doctor.phone_number
                    updated_email = email if email is not None else doctor.email
                    updated_specialty = specialty if specialty is not None else doctor.specialty
                    # Hospital ID: use the new ID, or if not provided, the current hospital's ID (or None if no hospital)
                    updated_hospital_id = hospital_id if hospital_id is not None else (doctor.hospital.pk if doctor.hospital else None)
                    updated_license_number = license_number if license_number is not None else doctor.license_number

                    # **1. Basic Validation: All fields are required**
                    if not all([updated_full_name, updated_date_of_birth, updated_gender, updated_nationality, updated_address,
                                updated_phone_number, updated_email, updated_specialty, updated_hospital_id, updated_license_number]):
                        return JsonResponse({'success': False, 'error': "All fields are required. Please fill out the form completely."}, status=400)

                    # **2. Validate Email Format** (only if email changed)
                    if updated_email and (updated_email != doctor.email):
                        try:
                            validate_email(updated_email)
                        except ValidationError:
                            return JsonResponse({'success': False, 'error': 'Invalid email format.'}, status=400)

                    # **3. Validate Rwandan Phone Number Format** (only if phone number changed)
                    if updated_phone_number and (updated_phone_number != doctor.phone_number):
                        if not validate_rwanda_phone(updated_phone_number):
                            return JsonResponse({'success': False, 'error': "Invalid Rwandan phone number format. Examples: +25078XXXXXXX or 078XXXXXXX."}, status=400)

                    # **4. Uniqueness Check: Phone Number** (excluding the current doctor being edited)
                    if updated_phone_number and (updated_phone_number != doctor.phone_number) and \
                       Doctor.objects.filter(phone_number=updated_phone_number).exclude(pk=doctor_id).exists():
                        return JsonResponse({'success': False, 'error': f"A doctor with the phone number '{updated_phone_number}' already exists."}, status=409) # 409 Conflict

                    # **5. Uniqueness Check: Email** (excluding the current doctor being edited)
                    if updated_email and (updated_email != doctor.email) and \
                       Doctor.objects.filter(email=updated_email).exclude(pk=doctor_id).exists():
                        return JsonResponse({'success': False, 'error': f"A doctor with the email '{updated_email}' already exists."}, status=409)

                    # **6. Uniqueness Check: License Number** (excluding the current doctor being edited)
                    if updated_license_number and (updated_license_number != doctor.license_number) and \
                       Doctor.objects.filter(license_number=updated_license_number).exclude(pk=doctor_id).exists():
                        return JsonResponse({'success': False, 'error': f"A doctor with the license number '{updated_license_number}' already exists."}, status=409)

                    # **7. Hospital Approval Status Check**
                    hospital = None
                    if updated_hospital_id: # Only try to fetch if an ID is provided
                        try:
                            # Ensure the selected hospital exists and is approved
                            hospital = get_object_or_404(Facility, pk=updated_hospital_id, is_approved='Approved')
                        except Facility.DoesNotExist:
                            return JsonResponse({'success': False, 'error': 'Selected hospital not found or not approved.'}, status=400)
                    # If updated_hospital_id is None, it means the client might want to unset the hospital, which is allowed.

                    # If all validations pass, update the doctor object
                    doctor.full_name = updated_full_name
                    doctor.date_of_birth = updated_date_of_birth
                    doctor.gender = updated_gender
                    doctor.nationality = updated_nationality
                    doctor.address = updated_address
                    doctor.phone_number = updated_phone_number
                    doctor.email = updated_email
                    doctor.specialty = updated_specialty
                    doctor.license_number = updated_license_number
                    doctor.hospital = hospital # Assign the validated hospital object (or None)

                    doctor.save() # Save changes to the database

                    # Return success JSON response with updated doctor data
                    return JsonResponse({
                        'success': True,
                        'message': 'Doctor updated successfully!',
                        'doctor': {
                            'id': doctor.id,
                            'full_name': doctor.full_name,
                            'date_of_birth': str(doctor.date_of_birth) if doctor.date_of_birth else None,
                            'gender': doctor.gender,
                            'nationality': doctor.nationality,
                            'phone_number': doctor.phone_number,
                            'address': doctor.address,
                            'email': doctor.email,
                            'specialty': doctor.specialty,
                            'hospital_name': doctor.hospital.name if doctor.hospital else 'N/A',
                            'license_number': doctor.license_number,
                        }
                    })
                except Doctor.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Doctor not found.'}, status=404)
                except InterruptedError as e: # Catch database integrity errors (e.g., unexpected unique constraint violation)
                    logger.error(f"Integrity error editing doctor {doctor_id}: {e}", exc_info=True)
                    return JsonResponse({'success': False, 'error': "An internal database error occurred (possible duplicate entry). Please try again."}, status=500)
                except Exception as e: # Catch any other unexpected errors during edit
                    logger.error(f"An unexpected error occurred while editing doctor {doctor_id}: {e}", exc_info=True)
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
                # --- End Edit Doctor Logic ---

            elif action == 'delete':
                # --- Start Delete Doctor Logic ---
                try:
                    doctor = get_object_or_404(Doctor, pk=doctor_id)
                    doctor_name = doctor.full_name
                    doctor.delete() # Delete the doctor record
                    return JsonResponse({'success': True, 'message': f'Doctor "{doctor_name}" deleted successfully!'})
                except Doctor.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Doctor not found.'}, status=404)
                except Exception as e: # Catch any errors during deletion
                    logger.error(f"Error deleting doctor {doctor_id}: {e}", exc_info=True)
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
                # --- End Delete Doctor Logic ---

            else:
                return JsonResponse({'success': False, 'error': 'Invalid action specified.'}, status=400)

        except json.JSONDecodeError: # Handles cases where the request body is not valid JSON
            return JsonResponse({'success': False, 'error': 'Invalid JSON in request body.'}, status=400)
        except Exception as e: # General error handling for the POST request
            logger.error(f"Error in manage_doctors POST handler: {e}", exc_info=True)
            return JsonResponse({'success': False, 'error': f"An unexpected server error occurred: {str(e)}"}, status=500)

    # Handles GET requests (for initially loading the page with the doctor list)
    else:
        # Fetch all doctors, prefetching related hospital data for efficiency
        doctors = Doctor.objects.select_related('hospital').all()
        # Fetch only approved hospitals for the dropdown in the edit modal
        hospitals = Facility.objects.filter(is_approved='Approved')

        context = {
            'doctors': doctors,
            'hospitals': hospitals,
        }
        return render(request, 'manage_hospital/manage_doctors.html', context)

def validate_rwanda_phone(phone_number):
    """
    Validates if a phone number matches common Rwandan formats.
    Accepts formats like:
    +2507XXXXXXXX (e.g., +250788123456, +250722123456, +250733123456)
    07XXXXXXXX (e.g., 0788123456, 0722123456, 0733123456)
    """
    # Regex for +2507X followed by 8 digits OR 07X followed by 8 digits
    # Covers +25078, +25079, +25073, +25072, +25070, +25071
    # Note: Adjust regex if specific prefixes (e.g., only 078, 079) are required.
    rwanda_phone_pattern = r'^(?:\+250|0)7[892301][0-9]{7}$'
    return re.match(rwanda_phone_pattern, phone_number) is not None


def add_doctor(request):
    # Fetch only hospitals where 'is_approved' field's value is the string 'Approved'
    hospitals = Facility.objects.filter(is_approved='Approved')

    if request.method == 'POST':
        # Retrieve form data
        full_name = request.POST.get('full_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        nationality = request.POST.get('nationality')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        specialty = request.POST.get('specialty')
        hospital_id = request.POST.get('hospital')
        license_number = request.POST.get('license_number')

        # Basic validation (all fields required by HTML, but good to double check)
        if not all([full_name, date_of_birth, gender, nationality, address,
                    phone_number, email, specialty, hospital_id, license_number]):
            messages.error(request, "All fields are required. Please fill out the form completely.")
            return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})

        try:
            # Validate email format
            validate_email(email)

            # Validate Rwandan phone number format
            if not validate_rwanda_phone(phone_number):
                messages.error(request, "Invalid Rwandan phone number format. Examples: +25078XXXXXXX or 078XXXXXXX.")
                return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})

            # Check for phone number uniqueness
            if Doctor.objects.filter(phone_number=phone_number).exists():
                messages.error(request, f"A doctor with the phone number '{phone_number}' already exists.")
                return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})

            # Check for email uniqueness
            if Doctor.objects.filter(email=email).exists():
                messages.error(request, f"A doctor with the email '{email}' already exists.")
                return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})

            # --- NEW: Check for license number uniqueness ---
            if Doctor.objects.filter(license_number=license_number).exists():
                messages.error(request, f"A doctor with the license number '{license_number}' already exists.")
                return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})
            # --- END NEW CHECK ---

            # Retrieve the hospital object, ensuring its 'is_approved' status is 'Approved'
            hospital = get_object_or_404(Facility, pk=hospital_id, is_approved='Approved')

            # Create and save the new Doctor object
            Doctor.objects.create(
                full_name=full_name,
                date_of_birth=date_of_birth,
                gender=gender,
                nationality=nationality,
                address=address,
                phone_number=phone_number,
                email=email,
                specialty=specialty,
                hospital=hospital,
                license_number=license_number
            )

            messages.success(request, f"Doctor '{full_name}' added successfully!")
            return redirect('manage_doctors') # Redirect to the doctor list after successful addition

        except ValidationError as e:
            messages.error(request, f"Validation Error: {e.message}")
            return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})
        except InterruptedError as e:
            logger.error(f"Integrity error adding doctor: {e}", exc_info=True)
            messages.error(request, "An internal error occurred (possible duplicate entry). Please try again.")
            return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})

    return render(request, 'manage_hospital/add_doctor.html', {'hospitals': hospitals})

def manage_hospital_inventory(request, id=None):
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        inventory_list = request.POST.get('inventory_list')
        
        try:
            # Check if inventory already exists for this hospital
            existing_inventory = HospitalInventory.objects.filter(hospital_id=hospital_id).first()
            
            if existing_inventory:
                return JsonResponse({
                    'success': False,
                    'message': 'Inventory already exists for this hospital. You can only edit or delete it.'
                })
            
            # Create new inventory
            inventory = HospitalInventory(
                hospital_id=hospital_id,
                inventory_list=inventory_list
            )
            inventory.save()
            
            # Get the hospital name for the response
            hospital = inventory.hospital
            
            return JsonResponse({
                'success': True,
                'message': 'Inventory added successfully',
                'id': inventory.id,
                'hospital_name': hospital.name,
                'inventory_list': inventory.inventory_list,
                'created_at': inventory.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            logger.error(f"Error saving inventory: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error saving inventory. Please try again.'
            })
    
    try:
        hospitals = Facility.objects.filter(is_approved='Approved')
        
        # Check for inventory ID in both URL path and query parameters
        inventory_id = id or request.GET.get('id')
        
        if inventory_id:  # Handle inventory details view
            try:
                inventory = HospitalInventory.objects.get(id=inventory_id)
                context = {
                    'inventory': inventory
                }
                return render(request, 'manage_hospital/inventory_details.html', context)
            except HospitalInventory.DoesNotExist:
                messages.error(request, 'Inventory not found')
                return redirect('manage_hospital_inventory')
        
        inventories = HospitalInventory.objects.all()
        context = {
            'hospitals': hospitals,
            'inventories': inventories
        }
        return render(request, 'manage_hospital/manage_hospital_inventory.html', context)
        
    except Exception as e:
        logger.error(f"Error in manage_hospital_inventory: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while loading the inventory list.")
        return render(request, 'manage_hospital/manage_hospital_inventory.html', {'hospitals': hospitals})

@require_GET
def view_hospital_inventory(request, inventory_id):
    try:
        inventory = HospitalInventory.objects.get(id=inventory_id)
        return JsonResponse({
            'success': True,
            'data': {
                'hospital': inventory.hospital.name,
                'inventory_list': inventory.inventory_list,
                'created_at': inventory.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except HospitalInventory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Inventory not found'
        })

def edit_hospital_inventory(request, inventory_id):
    try:
        inventory = HospitalInventory.objects.get(id=inventory_id)
        
        if request.method == 'POST':
            inventory_list = request.POST.get('inventory_list')
            
            if inventory_list:
                inventory.inventory_list = inventory_list
                inventory.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Inventory updated successfully',
                    'id': inventory.id,
                    'hospital_name': inventory.hospital.name,
                    'inventory_list': inventory.inventory_list,
                    'created_at': inventory.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Inventory list cannot be empty'
                })
        else:  # GET request
            # Return the current inventory data
            return JsonResponse({
                'success': True,
                'inventory': {
                    'id': inventory.id,
                    'hospital_name': inventory.hospital.name,
                    'inventory_list': inventory.inventory_list,
                    'created_at': inventory.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
            
    except HospitalInventory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Inventory not found'
        })
        
    except Exception as e:
        logger.error(f"Error updating inventory: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error updating inventory. Please try again.'
        })

@require_POST
def delete_hospital_inventory(request, inventory_id):
    try:
        inventory = HospitalInventory.objects.get(id=inventory_id)
        inventory.delete()
        return JsonResponse({
            'success': True,
            'message': 'Inventory deleted successfully'
        })
    except HospitalInventory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Inventory not found'
        })
    except Exception as e:
        logger.error(f"Error deleting inventory: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error deleting inventory. Please try again.'
        })

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import requests

import requests
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
# No need for cloudinary.utils here since we're not generating signed URLs

def download_hospital_credentials(request, facility_id):
    try:
        # Get the FacilityDocument instance from your database
        document = FacilityDocument.objects.get(facility_id=facility_id)

        # Construct the direct Cloudinary URL for download.
        # This assumes:
        # 1. The file was uploaded with 'public' access_mode via the preset.
        # 2. 'document.cloudinary_public_id' correctly stores the public ID (e.g., 'rwandaHealthConnect/your_filename').
        # 3. 'fl_attachment' transformation is used to force download.
        download_url = (
            f"https://res.cloudinary.com/dom9oqh7m/raw/upload/fl_attachment/"
            f"{document.cloudinary_public_id}"
        )

        # For debugging: print the URL being used to fetch the file
        print(f"DEBUG: Attempting to download from URL: {download_url}")

        # Fetch the file content from Cloudinary
        response_from_cloudinary = requests.get(download_url, stream=True)
        response_from_cloudinary.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Prepare Django's HttpResponse to send the file to the user
        filename = f"{document.facility.name.replace(' ', '_')}_credentials.zip"
        django_response = HttpResponse(
            response_from_cloudinary.iter_content(chunk_size=8192), # Stream content for efficiency
            content_type='application/zip' # Ensures browser treats it as a ZIP file
        )
        django_response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return django_response

    except FacilityDocument.DoesNotExist:
        messages.error(request, "No documents found for this facility.")
        return redirect('evaluate_hospital_credentials')
    except requests.exceptions.RequestException as e:
        # Catch network issues or HTTP errors (like 404 Not Found, or 401 if an old 'authenticated' file is attempted)
        error_message = f"Error downloading documents: {e}"
        if e.response is not None:
            error_message += f" (Status: {e.response.status_code}, Response: {e.response.text})"
        messages.error(request, error_message)
        print(f"DEBUG: Cloudinary Request Error: {error_message}") # Print error details for server logs
        return redirect('evaluate_hospital_credentials')
    except Exception as e:
        # Catch any other unexpected errors
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        print(f"DEBUG: Unexpected Error: {str(e)}") # Print unexpected error for server logs
        return redirect('evaluate_hospital_credentials')
def evaluate_hospital_credentials(request):
    # Get all facility documents with their related facility information
    facility_documents = FacilityDocument.objects.select_related('facility').all()

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(facility_documents, 10)  # Show 10 documents per page

    try:
        facility_documents = paginator.page(page)
    except PageNotAnInteger:
        facility_documents = paginator.page(1)
    except EmptyPage:
        facility_documents = paginator.page(paginator.num_pages)

    context = {
        'facility_documents': facility_documents
    }
    return render(request, 'manage_hospital/evaluate_hospital.html', context)


from django.shortcuts import render, redirect
from accounts.models import Facility # Assuming Facility is in accounts.models
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist # Import ObjectDoesNotExist

def request_credentials_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            facility = Facility.objects.get(admin_email=email)
            request.session['facility_email'] = email
            request.session['admin_first_name'] = facility.admin_first_name
            request.session['admin_last_name'] = facility.admin_last_name
            return redirect('upload_documents')
        except ObjectDoesNotExist:
            messages.error(request, 'The email you entered does not exist in our system.')
            # Use the correct URL name for redirection
            return redirect('request_credentials_email') # Changed from 'request_credentials'
    # Use the correct URL name for redirection in the initial GET request if needed
    return render(request, 'accounts/request_credentials.html')
from django.http import JsonResponse
from .models import FacilityDocument  # Added the new model
import json


from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, render
from .models import FacilityDocument # Updated import
from django.db import connection

from django.utils.timezone import now


def upload_documents(request):
    if 'facility_email' not in request.session:
        return redirect('request_credentials')

    facility = None
    try:
        facility = Facility.objects.get(admin_email=request.session['facility_email'])
    except Facility.DoesNotExist:
        messages.error(request, 'Facility not found for your email. Please register.')
        return redirect('register')

        # Check if facility has already submitted documents using ORM
    has_submitted = FacilityDocument.objects.filter(facility=facility).exists()

    if request.method == 'POST':
        if has_submitted:
            messages.warning(request, 'You have already submitted your hospital credentials.')
            return redirect('upload_documents')

        cloudinary_url = request.POST.get('cloudinary_url')
        public_id = request.POST.get('public_id')

        if not cloudinary_url or not public_id:
            messages.error(request, 'Missing document information')
            return redirect('upload_documents')

        try:
            # THIS IS THE MODIFIED SECTION: Use Django's ORM instead of raw SQL for insertion
            FacilityDocument.objects.create(
                facility=facility,
                document_type='Combined ZIP',  # Default value for this form
                cloudinary_url=cloudinary_url,
                cloudinary_public_id=public_id,
                is_zip_archive=True  # Assuming this form always uploads a ZIP
                # 'uploaded_at' field is automatically set by auto_now_add=True in the model
            )

            messages.success(request, 'Documents submitted successfully!')
            return redirect('success_page')  # Keeping your original redirect URL

        except Exception as e:
            # Log the full exception for better debugging (e.g., to console or file)
            print(f"Error saving FacilityDocument via ORM: {e}")
            messages.error(request, f'Error: {str(e)}')  # Kept your original error message format
            return redirect('upload_documents')

    # For GET requests (rendering the form)
    admin_first_name = request.session.get('admin_first_name', '')
    admin_last_name = request.session.get('admin_last_name', '')

    # Combine first and last names for the display name
    admin_display_name = f"{admin_first_name} {admin_last_name}".strip()

    # If after stripping, the name is empty (e.g., both were empty strings),
    # then use 'Valued User' as the fallback.
    if not admin_display_name:
        admin_display_name = 'Valued User'

    context = {
        'admin_name': admin_display_name,
        'cloudinary_cloud_name': settings.CLOUDINARY_CLOUD_NAME,
        'cloudinary_upload_preset': settings.CLOUDINARY_UPLOAD_PRESET,
        'has_submitted': has_submitted  # Pass the actual check to the template
    }

    return render(request, 'accounts/upload_documents.html', context)
def success_page(request):
    context = {
        'admin_first_name': request.session.get('admin_first_name', ''),
        'admin_last_name': request.session.get('admin_last_name', ''),
    }
    return render(request, 'accounts/success_page.html', context)

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.core.validators import validate_email, ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import re
from datetime import datetime, date  # Import 'date'
from .utils.sms import send_sms
import logging

from accounts.models import User, Facility

logger = logging.getLogger(__name__)


def normalize_phone_number(raw_phone):
    """Normalizes a Rwandan phone number input to the +2507XXXXXXXX format."""
    processed_phone = raw_phone.strip()
    if processed_phone:
        if processed_phone.startswith('07'):
            processed_phone = '+250' + processed_phone[1:]
        elif len(processed_phone) == 9 and processed_phone.startswith('7'):
            processed_phone = '+250' + processed_phone
    return processed_phone




@login_required
def admin_details(request):
    """Displays a list of all users with pagination."""
    try:
        users = User.objects.all().select_related('hospital')
        from django.core.paginator import Paginator
        paginator = Paginator(users, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'manage_hospital/admin_details.html', {
            'users': page_obj
        })
    except Exception as e:
        logger.error(f"Error in admin_details view: {str(e)}", exc_info=True)
        messages.error(request, f'Error loading user data: {str(e)}')
        return render(request, 'manage_hospital/admin_details.html', {
            'error': str(e)
        })


@login_required
def update_user(request):
    """Handles the update of user accounts with proper JSON responses."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        user_id = request.POST.get('id')
        user_to_update = User.objects.get(id=user_id)

        original_role = user_to_update.role
        original_hospital = user_to_update.hospital
        # Ensure original values are strings for consistent comparison, handling None
        original_email = user_to_update.email if user_to_update.email is not None else ''
        original_phone = user_to_update.phone if user_to_update.phone is not None else ''
        original_license_number = user_to_update.license_number if user_to_update.license_number is not None else ''

        # Extract and normalize fields
        raw_phone = request.POST.get('phone', '').strip()
        processed_phone = normalize_phone_number(raw_phone)
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        new_role = request.POST.get('role', original_role).strip()
        new_hospital_id = request.POST.get('hospital_id', '').strip()
        new_license_number = request.POST.get('license_number', '').strip() if new_role == 'hospital' else None
        address = request.POST.get('address', '').strip()
        raw_date_of_birth = request.POST.get('date_of_birth', '').strip()  # Get raw string
        gender = request.POST.get('gender', '').strip()
        is_active = request.POST.get('is_active') == '1'
        new_password = request.POST.get('password', '').strip()

        errors = []
        parsed_date_of_birth = None  # Initialize parsed date_of_birth

        # Required field checks
        if not first_name:
            errors.append("First Name is required.")
        if not last_name:
            errors.append("Last Name is required.")
        if not email:
            errors.append("Email is required.")

        # Date of Birth parsing and validation
        if not raw_date_of_birth:
            errors.append("Date of Birth is required.")
        else:
            try:
                # Parse the raw date string into a date object
                parsed_date_of_birth = datetime.strptime(raw_date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid Date of Birth format. Please use YYYY-MM-DD.")

        if new_role != 'admin':
            if not processed_phone:
                errors.append("Phone Number is required.")
            if not address:
                errors.append("Address is required.")
        else:
            processed_phone = None
            address = None
            # Ensure license_number is None if role is not hospital
            new_license_number = None

        # Email format validation
        try:
            validate_email(email)
        except ValidationError:
            errors.append("Invalid email format.")

        # Phone format validation
        if processed_phone and not validate_rwanda_phone(processed_phone):
            errors.append("Invalid Rwandan phone number format. Please use +2507XXXXXXXX.")

        # Check for existing email and phone (excluding current user)
        # Added 'if email and email != original_email' to prevent self-clash
        if email and email != original_email and User.objects.filter(email=email).exclude(id=user_id).exists():
            errors.append(f"Email '{email}' already exists for another user.")
        if processed_phone and processed_phone != original_phone and User.objects.filter(phone=processed_phone).exclude(
                id=user_id).exists():
            errors.append(f"Phone number '{processed_phone}' already exists for another user.")

        # Hospital admin logic
        target_hospital_instance = None
        if new_role == 'hospital':
            if not new_hospital_id:
                errors.append("Please select an approved hospital for Hospital Administrator.")
            else:
                try:
                    target_hospital_instance = Facility.objects.get(id=new_hospital_id, is_approved='Approved')
                except Facility.DoesNotExist:
                    errors.append("Selected hospital is not approved or does not exist.")

                # Check if another user is already admin for this specific hospital (excluding current user)
                if target_hospital_instance and User.objects.filter(
                        role='hospital', hospital=target_hospital_instance
                ).exclude(id=user_id).exists():
                    errors.append(f"The hospital '{target_hospital_instance.name}' already has an administrator.")

            if not new_license_number:
                errors.append("License Number is required for Hospital Administrators.")
            # Added check for 'if new_license_number and new_license_number != original_license_number'
            elif new_license_number and new_license_number != original_license_number and User.objects.filter(
                    license_number=new_license_number).exclude(id=user_id).exists():
                errors.append(f"License number '{new_license_number}' already exists for another user.")
        else:
            new_license_number = None
            target_hospital_instance = None

        # Phone conflict with Facility admin (more robust exclusion)
        facilities_to_exclude_from_clash_check_ids = []
        if original_hospital:
            facilities_to_exclude_from_clash_check_ids.append(original_hospital.id)
        if target_hospital_instance:
            if target_hospital_instance.id not in facilities_to_exclude_from_clash_check_ids:
                facilities_to_exclude_from_clash_check_ids.append(target_hospital_instance.id)

        if processed_phone and processed_phone != original_phone:
            existing_facility = Facility.objects.filter(admin_phone=processed_phone).exclude(
                id__in=facilities_to_exclude_from_clash_check_ids
            ).first()
            if existing_facility:
                errors.append(
                    f"The phone number '{processed_phone}' is already used as an admin phone for another hospital ('{existing_facility.name}')."
                )

        # Email conflict with Facility admin
        if email and email != original_email:
            existing_facility_email_clash = Facility.objects.filter(admin_email=email).exclude(
                id__in=facilities_to_exclude_from_clash_check_ids
            ).first()
            if existing_facility_email_clash:
                errors.append(
                    f"The email '{email}' is already registered as an administrator email for "
                    f"another hospital ('{existing_facility_email_clash.name}'). Please use a different email."
                )

        if errors:
            return JsonResponse({
                'status': 'error',
                'message': '\n'.join(errors),
                'errors': {
                    # Improved error flags for frontend to check specific field errors
                    'first_name': any('first name' in e.lower() for e in errors),
                    'last_name': any('last name' in e.lower() for e in errors),
                    'email': any('email' in e.lower() for e in errors),
                    'phone': any('phone number' in e.lower() for e in errors),
                    'address': any('address' in e.lower() for e in errors),
                    'date_of_birth': any('date of birth' in e.lower() for e in errors),
                    'hospital_id': any('hospital' in e.lower() for e in errors),
                    'license_number': any('license number' in e.lower() for e in errors)
                }
            }, status=400)

        # Proceed with database update
        with transaction.atomic():
            # Clean up old hospital admin reference
            if original_role == 'hospital' and original_hospital:
                # Only clear if changing role or changing hospital, AND original admin details match this user
                remove_from_old_hospital = (
                        new_role != 'hospital' or
                        (
                                    new_role == 'hospital' and target_hospital_instance and original_hospital.id != target_hospital_instance.id)
                )
                if remove_from_old_hospital:
                    # Check if the facility's admin email/phone truly belongs to this user before clearing
                    if (
                            original_hospital.admin_email == original_email and original_hospital.admin_phone == original_phone) or \
                            (original_hospital.admin_email == original_email and not original_hospital.admin_phone) or \
                            (original_hospital.admin_phone == original_phone and not original_hospital.admin_email):
                        original_hospital.admin_first_name = None
                        original_hospital.admin_last_name = None
                        original_hospital.admin_email = None
                        original_hospital.admin_phone = None
                        original_hospital.save()

            # Update user data
            user_to_update.first_name = first_name
            user_to_update.last_name = last_name
            user_to_update.email = email
            user_to_update.phone = processed_phone
            user_to_update.address = address
            user_to_update.date_of_birth = parsed_date_of_birth  # Assign the parsed date object
            user_to_update.gender = gender
            user_to_update.role = new_role
            user_to_update.is_active = is_active
            user_to_update.license_number = new_license_number
            user_to_update.hospital = target_hospital_instance

            if new_password:
                user_to_update.set_plain_password(new_password)

            user_to_update.save()

            # Update new hospital admin info
            if new_role == 'hospital' and target_hospital_instance:
                target_hospital_instance.admin_first_name = first_name
                target_hospital_instance.admin_last_name = last_name
                target_hospital_instance.admin_email = email
                target_hospital_instance.admin_phone = processed_phone
                target_hospital_instance.save()

        # Send SMS notification
        if processed_phone and validate_rwanda_phone(processed_phone):
            sms_message = (
                f"DEAR {first_name.upper()} {last_name.upper()},\n\n"
                f"YOUR ACCOUNT DETAILS FOR RWANDA HEALTH CONNECT REFERRAL SYSTEM HAVE BEEN UPDATED.\n\n"
                f"LOGIN CREDENTIALS:\n"
                f"  EMAIL: {email}\n"
                f"PASSWORD: {'(Unchanged)' if not new_password else 'has been reset (new password sent separately if applicable)'}\n\n"  # More secure message
                "PLEASE KEEP YOUR CREDENTIALS SAFE AND CONTACT SUPPORT IF NEEDED.\n\n"
                "THANK YOU."
            )
            sms_result = send_sms(processed_phone, sms_message)
            logger.info(f"SMS update status for {email}: {sms_result.get('status')} - {sms_result.get('message')}")

        return JsonResponse({
            'status': 'success',
            'message': f"User {first_name} {last_name} updated successfully.",
            'user': {  # Nest user data under 'user' key for cleaner frontend access
                'id': user_to_update.id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': processed_phone or '',
                'address': address or '',
                # Crucial Fix: Check if it's a date object before calling strftime
                'date_of_birth': user_to_update.date_of_birth.strftime('%Y-%m-%d') if isinstance(
                    user_to_update.date_of_birth, date) else '',
                'gender': gender,
                'role': new_role,
                'hospital_id': target_hospital_instance.id if target_hospital_instance else '',
                'hospital_name': target_hospital_instance.name if target_hospital_instance else 'N/A',
                'is_active': is_active,
                'license_number': new_license_number or '',
                'created_at': user_to_update.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': user_to_update.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    except User.DoesNotExist:
        logger.warning(f"User with ID {user_id} not found.")
        return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error updating user: {str(e)}", exc_info=True)
        # Improved error message for duplicate entries
        if 'Duplicate entry' in str(e):
            error_detail = "A duplicate entry was found for a unique field (e.g., email or phone number). Please check the entered data."
        else:
            error_detail = f"An unexpected error occurred: {str(e)}"
        return JsonResponse({'status': 'error', 'message': error_detail}, status=500)  # Use 500 for true server errors
@login_required
def delete_user(request, user_id):
    """Deletes a user with proper JSON response."""
    if request.method == 'POST':
        try:
            user_to_delete = User.objects.get(id=user_id)
            user_name = f"{user_to_delete.first_name} {user_to_delete.last_name}"
            user_to_delete.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'User {user_name} deleted successfully.'
            })
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': f'Failed to delete user: {str(e)}'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
@csrf_exempt
def update_facility(request):
    try:
        facility_id = request.POST.get('id')
        if not facility_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Facility ID is required',
                'field': 'facilityId'
            }, status=400)

        with connection.cursor() as cursor:
            # Debug: Log received data
            print("Received update data:", request.POST.dict())

            # Check if facility exists
            cursor.execute("SELECT id FROM accounts_facility WHERE id=%s", [facility_id])
            if not cursor.fetchone():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Facility not found',
                    'field': 'facilityId'
                }, status=404)

            # Check for duplicate email (excluding current facility)
            cursor.execute(
                "SELECT id FROM accounts_facility WHERE admin_email=%s AND id!=%s",
                [request.POST.get('admin_email'), facility_id]
            )
            if cursor.fetchone():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already exists',
                    'field': 'adminEmail'
                }, status=400)

            # Check for duplicate phone (excluding current facility)
            cursor.execute(
                "SELECT id FROM accounts_facility WHERE admin_phone=%s AND id!=%s",
                [request.POST.get('admin_phone'), facility_id]
            )
            if cursor.fetchone():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Phone number already exists',
                    'field': 'adminPhone'
                }, status=400)

            # Prepare update data - modified to accept any string for is_approved
            update_fields = {
                'name': request.POST.get('name'),
                'facility_type': request.POST.get('facility_type'),
                'facility_level': request.POST.get('facility_level'),
                'is_approved': request.POST.get('is_approved'),  # Changed from boolean conversion
                'address': request.POST.get('address'),
                'province': request.POST.get('province'),
                'district': request.POST.get('district'),
                'sector': request.POST.get('sector'),
                'cell': request.POST.get('cell'),
                'village': request.POST.get('village'),
                'admin_email': request.POST.get('admin_email'),
                'admin_first_name': request.POST.get('admin_first_name'),
                'admin_last_name': request.POST.get('admin_last_name'),
                'admin_phone': request.POST.get('admin_phone'),
                'admin_position': request.POST.get('admin_position'),
                'updated_at': datetime.now()
            }

            # Debug: Log the update query
            print("Update query:", """
                UPDATE accounts_facility SET
                    name = %s,
                    facility_type = %s,
                    facility_level = %s,
                    is_approved = %s,
                    address = %s,
                    province = %s,
                    district = %s,
                    sector = %s,
                    cell = %s,
                    village = %s,
                    admin_email = %s,
                    admin_first_name = %s,
                    admin_last_name = %s,
                    admin_phone = %s,
                    admin_position = %s,
                    updated_at = %s
                WHERE id = %s
            """, tuple(update_fields.values()) + (facility_id,))

            # Execute update
            cursor.execute("""
                UPDATE accounts_facility SET
                    name = %s,
                    facility_type = %s,
                    facility_level = %s,
                    is_approved = %s,
                    address = %s,
                    province = %s,
                    district = %s,
                    sector = %s,
                    cell = %s,
                    village = %s,
                    admin_email = %s,
                    admin_first_name = %s,
                    admin_last_name = %s,
                    admin_phone = %s,
                    admin_position = %s,
                    updated_at = %s
                WHERE id = %s
            """, tuple(update_fields.values()) + (facility_id,))

            # Verify update
            cursor.execute("SELECT * FROM accounts_facility WHERE id=%s", [facility_id])
            updated_facility = cursor.fetchone()
            print("Updated facility:", updated_facility)

            return JsonResponse({
                'status': 'success',
                'message': 'Facility updated successfully',
                'updated_at': update_fields['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to update facility: {str(e)}'
        }, status=500)






@login_required
@require_POST
def request_credentials_sms(request):
    try:
        # Parse request data
        data = json.loads(request.body)
        facility_id = data.get('facility_id')
        phone = data.get('phone')

        if not all([facility_id, phone]):
            return JsonResponse({
                'status': 'error',
                'message': 'Missing facility_id or phone'
            }, status=400)

        # Get facility details
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Facility not found'
            }, status=404)

        message = f"""Dear {facility.admin_first_name or 'Admin'},

        Your hospital credentials are due.
        Please visit the Rwanda Health Connect site and click "Provide Registration Credentials" at the bottom of the login form to upload a single ZIP file.
        Use your registered email: {facility.admin_email}.
        A full list of required credentials will be available after login. Note: This is a one-time submission.

        Thank you,
        {settings.SITE_NAME} Team"""

        # Send SMS
        sms_response = send_sms(phone, message)

        # Create audit log
        CredentialsRequest.objects.create(
            facility=facility,
            requested_by=request.user,
            phone=phone,
            message=message,
            status='sent' if sms_response.get('status') == 'success' else 'failed',
            response=sms_response
        )

        return JsonResponse({
            'status': sms_response.get('status'),
            'message': sms_response.get('message', 'SMS processed'),
            'sms_response': sms_response
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

from django.db import IntegrityError, transaction # Import transaction and IntegrityError

@require_POST
@csrf_exempt
def delete_facility(request, facility_id):
    try:
        # Use a transaction to ensure atomicity
        with transaction.atomic():
            # Get the facility object using Django's ORM
            facility = Facility.objects.get(id=facility_id)

            # Deleting the facility using ORM will trigger on_delete behaviors
            # defined in your models (e.g., CASCADE for FacilityDocument,
            # HospitalInventory, CredentialsRequest, and SET_NULL for Doctor).
            facility.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Facility deleted successfully'
            })

    except Facility.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Facility not found'
        }, status=404)
    except IntegrityError:
        # This specific error might occur if SET_NULL fails due to database
        # constraints not allowing NULL, or if there's an unforeseen foreign key
        # not handled by CASCADE/SET_NULL (less likely with your current models).
        return JsonResponse({
            'status': 'error',
            'message': 'Cannot delete facility due to related records. Ensure all related records are properly handled or deleted first.'
        }, status=409) # 409 Conflict is appropriate for this type of error
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to delete facility: {str(e)}'
        }, status=500)

def manage_hospital_view(request):
    return render(request, 'manage_hospital/manage_hospital.html')


def manage_hospital_registration_view(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                id, name, facility_type, facility_level, address,
                province, district, sector, cell, is_approved,
                created_at, updated_at, admin_email, admin_first_name,
                admin_last_name, admin_password, admin_phone, admin_position,
                village
            FROM accounts_facility
        """)
        facilities = cursor.fetchall()

    return render(request, 'manage_hospital/manage_hospital_registration.html', {'facilities': facilities})


# Add these imports at the top of your manage_hospital/views.py if they are not already there
from accounts.models import Facility
from manage_hospital.models import FacilityDocument  # Ensure FacilityDocument is imported
from django.db import transaction
import traceback  # Useful for debugging in case of unexpected errors


# --- Add this entire function to your manage_hospital/views.py file ---
@require_POST
@csrf_exempt  # You can consider removing this if you handle CSRF tokens properly in your JS headers
def delete_facility_documents(request, facility_id):
    """
    Deletes ALL FacilityDocument records associated with a given facility.
    It does NOT delete the Facility (hospital) record itself.
    """
    try:
        with transaction.atomic():  # Ensures that all or none of the deletions happen
            facility = get_object_or_404(Facility, id=facility_id)

            # Delete all documents linked to this specific facility
            deleted_count, _ = FacilityDocument.objects.filter(facility=facility).delete()

            if deleted_count > 0:
                return JsonResponse({
                    'status': 'success',
                    'message': f'Successfully deleted {deleted_count} document(s) for facility "{facility.name}".'
                })
            else:
                return JsonResponse({
                    'status': 'info',  # Use 'info' status if nothing was deleted but no error occurred
                    'message': f'No documents found for facility "{facility.name}" to delete.'
                })

    except Facility.DoesNotExist:
        # This handles the case where the facility_id provided doesn't exist
        return JsonResponse({
            'status': 'error',
            'message': 'Facility not found.'
        }, status=404)
    except Exception as e:
        # Catch any other unexpected errors during the deletion process
        traceback.print_exc()  # Prints the full traceback to your server console for debugging
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to delete documents: {str(e)}'
        }, status=500)


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.core.validators import validate_email, ValidationError
from django.contrib import messages  # Assuming messages framework is configured

# Assuming you have a .utils.sms.py and a .utils.validators.py
from .utils.sms import send_sms

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.core.validators import validate_email, ValidationError
from django.contrib import messages
import re  # Import re for regular expressions

# Assuming you have a .utils.sms.py
from .utils.sms import send_sms

# Import your models
from accounts.models import User, Facility


# --- MODIFICATION: Updated validate_rwanda_phone to strictly match +2507XXXXXXXX format ---
def validate_rwanda_phone(phone_number):
    """
    Validates Rwandan phone number to strictly match the +2507XXXXXXXX format.
    This function expects the phone_number to already include the '+250' prefix.
    Example valid: +250781234567 (13 characters)
    """
    # Regex for +2507 followed by exactly 8 digits
    pattern = re.compile(r"^\+2507[0-9]{8}$")
    return bool(pattern.match(phone_number))


def add_hospital_view(request):
    """
    Handles the creation of new user accounts, including hospital administrators.
    It ensures that if a 'hospital' role is selected, the chosen hospital
    is an approved facility before linking.
    It also adds '+250' prefix to 9-digit phone numbers and enforces one admin per hospital.
    """
    if request.method == 'POST':
        # Get form data, stripping whitespace and normalizing email
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        license_number = request.POST.get('license_number', '').strip()
        raw_phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '').strip()
        gender = request.POST.get('gender', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        role = request.POST.get('role', 'admin').strip()
        hospital_id = request.POST.get('hospital_id', '').strip()

        errors = []

        # --- Phone number processing (before validation) ---
        # If the input is '790000000', convert to '+250790000000'
        # If the input is '0790000000', convert to '+250790000000'
        # If the input is already '+250790000000', it remains unchanged.
        processed_phone = raw_phone
        if raw_phone:  # Only process if raw_phone is not empty
            # Normalize to +2507XXXXXXXX format for internal processing and saving
            if raw_phone.startswith('07'):
                processed_phone = '+250' + raw_phone[1:]  # e.g., 078xxxxxxx -> +25078xxxxxxx
            elif len(raw_phone) == 9 and raw_phone.startswith('7'):
                processed_phone = '+250' + raw_phone  # e.g., 78xxxxxxx -> +25078xxxxxxx
            elif not raw_phone.startswith('+250'):
                # For any other unhandled format that's not +250 or 07, default to just using raw_phone
                # This might indicate an invalid format already, which validate_rwanda_phone will catch.
                pass
                # Now, use processed_phone for all subsequent checks, saving, and SMS.

        hospital_instance = None
        if role == 'hospital' and hospital_id:
            try:
                hospital_instance = Facility.objects.get(id=hospital_id, is_approved='Approved')
            except Facility.DoesNotExist:
                errors.append("Selected hospital is not approved or does not exist.")
        elif role == 'admin':
            hospital_id = None
            license_number = None

        # Validate required fields
        required_fields = [
            ('first_name', 'First Name'), ('last_name', 'Last Name'), ('email', 'Email'),
            ('phone', 'Phone Number'), ('password', 'Password'), ('confirm_password', 'Confirm Password')
        ]
        if role == 'hospital':
            required_fields.append(('license_number', 'License Number'))

        for field_name, label in required_fields:
            if field_name == 'phone':
                if not processed_phone:
                    errors.append(f"{label} is required.")
            elif not request.POST.get(field_name, '').strip():
                errors.append(f"{label} is required.")

        # Check if passwords match
        if password and password != confirm_password:
            errors.append("Passwords do not match.")

        # --- MODIFICATION: Use the updated validate_rwanda_phone for validation ---
        if processed_phone and not validate_rwanda_phone(processed_phone):
            errors.append("Invalid Rwandan phone number format. Please use +2507XXXXXXXX.")

        # Check for existing records using User model
        if User.objects.filter(email=email).exists():
            errors.append("Email already exists.")

        if User.objects.filter(phone=processed_phone).exists():
            errors.append("Phone number already exists.")

        if role == 'hospital' and license_number and User.objects.filter(license_number=license_number).exists():
            errors.append("License number already exists.")

        # One admin per hospital validation
        if role == 'hospital' and hospital_instance:
            # Check if there's already an admin for THIS specific hospital
            existing_admin_for_hospital = User.objects.filter(role='hospital', hospital=hospital_instance).first()
            if existing_admin_for_hospital and existing_admin_for_hospital.email != email:
                # If an admin exists and it's not the user we're trying to update (by email)
                errors.append(f"The hospital '{hospital_instance.name}' already has an administrator registered.")

            # --- NEW VALIDATION: Check if this phone number is already an admin_phone for ANOTHER facility ---
            # This handles the "Duplicate entry for accounts_facility.admin_phone" error.
            # We exclude the current hospital_instance's admin_phone from the check if we are updating it.
            existing_facility_with_this_admin_phone = Facility.objects.filter(admin_phone=processed_phone).first()
            if existing_facility_with_this_admin_phone:
                if hospital_instance is None or existing_facility_with_this_admin_phone.id != hospital_instance.id:
                    # If the phone is found on another facility, OR
                    # if we are creating a *new* admin for a hospital and that phone
                    # is already taken by *any* facility's admin_phone.
                    errors.append(
                        f"The phone number '{processed_phone}' is already registered as an administrator phone for another hospital.")

        if errors:
            return render(request, 'manage_hospital/add_hospital.html', {
                'error_message': '\n'.join(errors),
                'form_data': {
                    'first_name': first_name, 'last_name': last_name, 'email': email,
                    'license_number': license_number, 'phone': raw_phone,  # Pass raw_phone back for display
                    'address': address, 'date_of_birth': date_of_birth,
                    'gender': gender, 'role': role, 'hospital_id': hospital_id
                }
            })

        try:
            with transaction.atomic():
                user_defaults = {
                    'first_name': first_name, 'last_name': last_name,
                    'license_number': license_number if role == 'hospital' else None,
                    'phone': processed_phone,  # Use processed_phone for saving
                    'address': address,
                    'date_of_birth': date_of_birth if date_of_birth else None,
                    'gender': gender, 'role': role,
                    'is_active': False, 'is_superuser': False, 'is_staff': False,
                    'hospital': hospital_instance,
                }

                user, created = User.objects.get_or_create(email=email, defaults=user_defaults)

                if not created:
                    for key, value in user_defaults.items():
                        setattr(user, key, value)
                    user.save()

                user.set_plain_password(password)

                if role == 'hospital' and hospital_instance:
                    facility = hospital_instance
                    facility.admin_first_name = first_name
                    facility.admin_last_name = last_name
                    facility.admin_email = email
                    facility.admin_phone = processed_phone  # Use processed_phone here too
                    facility.save()

                message = (
                    f"DEAR {first_name.upper()} {last_name.upper()},\n\n"
                    f"YOUR ACCOUNT FOR RWANDA HEALTH CONNECT REFERRAL SYSTEM HAS BEEN SUCCESSFULLY REGISTERED.\n\n"
                    f"LOGIN CREDENTIALS:\n"
                    f"  EMAIL: {email}\n"
                    f"PASSWORD: {password}\n\n"
                    "PLEASE KEEP YOUR CREDENTIALS SAFE\n\n"
                    "CONTACT US AT 0790878665 OR hyalliosn5050@gmail.com FOR SUPPORT.\n\n"
                    "YOUR ACCOUNT IS NOW READY."
                )

                sms_result = send_sms(processed_phone, message)
                sms_status = sms_result.get('status', 'error')
                sms_message = sms_result.get('message', 'Unknown error occurred')

            context = {
                'success_message': 'Administrator account added successfully!',
                'sms_content': message, 'phone_number': processed_phone,
                'sms_status': sms_status, 'sms_result_message': sms_message,
                'recipient_name': f"{first_name} {last_name}", 'form_data': {}
            }
            return render(request, 'manage_hospital/add_hospital.html', context)

        except Exception as e:
            print(f"Database error: {str(e)}")
            return render(request, 'manage_hospital/add_hospital.html', {
                'error_message': f'Registration failed due to a system error: {str(e)}',
                'form_data': {
                    'first_name': first_name, 'last_name': last_name, 'email': email,
                    'license_number': license_number, 'phone': raw_phone,
                    'address': address, 'date_of_birth': date_of_birth,
                    'gender': gender, 'role': role, 'hospital_id': hospital_id
                }
            })

    return render(request, 'manage_hospital/add_hospital.html', {
        'form_data': {}
    })





def get_approved_hospitals(request):
    """
    API endpoint to return a list of approved hospitals.
    """
    approved_hospitals = Facility.objects.filter(is_approved='Approved').values('id', 'name').order_by('name')
    return JsonResponse(list(approved_hospitals), safe=False)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM accounts_user WHERE email=%s AND password=%s", [email, password])
            user = cursor.fetchone()
            if user:
                # Update is_active to 1 and last_login to current date and time
                current_time = datetime.now()
                cursor.execute("UPDATE accounts_user SET is_active=1, last_login=%s WHERE email=%s", [current_time, email])
                # Proceed with login
                return redirect('home_page')
            else:
                return render(request, 'login.html', {'error': 'Invalid credentials'})

def logout_view(request):
    # Assuming user email is stored in session
    email = request.session.get('user_email')
    if email:
        with connection.cursor() as cursor:
            # Update is_active to 0 and last_login to 'pending'
            cursor.execute("UPDATE accounts_user SET is_active=0, last_login='pending' WHERE email=%s", [email])
    # Proceed with logout
    return redirect('login_page')




@require_POST
def request_credenti(request):
    try:
        data = json.loads(request.body)
        facility_id = data.get('facility_id')
        phone = data.get('phone')
        message = data.get('message')

        # Validate input
        if not all([facility_id, phone, message]):
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

        # Get facility and user
        facility = Facility.objects.get(id=facility_id)
        user = request.user

        # Send SMS
        sms_response = send_sms(phone, message)

        # Create record
        CredentialsRequest.objects.create(
            facility=facility,
            requested_by=user,
            phone=phone,
            message=message,
            status='sent' if sms_response.get('status') == 'success' else 'failed',
            response=sms_response
        )

        if sms_response.get('status') == 'success':
            return JsonResponse({
                'status': 'success',
                'message': 'SMS sent successfully',
                'sms_response': sms_response
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send SMS',
                'sms_response': sms_response
            }, status=500)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def send_verification_sms(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': False,
            'error': 'Invalid request method. Use POST.'
        }, status=405)

    phone = "+250790878665"  # Rwanda number
    message = "this is a test using django using the api key in real time my geeh"

    try:
        result = send_sms(phone, message)

        if result.get('status') == 'success':
            return JsonResponse({
                'status': True,
                'message': 'Message sent successfully!',
                'data': result.get('data', {}),
                'device_id': result.get('device_id')
            })
        else:
            error_response = {
                'status': False,
                'error': result.get('message', 'SMS sending failed'),
                'device_id': result.get('device_id'),
                'type': 'TextBee API Error'
            }

            if 'api_response' in result:
                error_response['api_response'] = result['api_response']
            if 'status_code' in result:
                error_response['status_code'] = result['status_code']

            return JsonResponse(error_response, status=400)

    except Exception as e:
        return JsonResponse({
            'status': False,
            'error': f'Internal server error: {str(e)}',
            'type': 'Server Error'
        }, status=500)


@login_required
def get_user_password(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({
            'status': 'success',
            'password': user.plain_password
        })
    except User.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)