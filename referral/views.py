# referral/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
import uuid
import logging

# Import your models
from .models import Referral
from patients.models import Patient
from manage_hospital.models import Facility, Doctor

# Ensure this path is correct for your SMS utility
# You MUST have this file and function implemented for SMS sending to work!
from manage_hospital.utils.sms import send_sms

logger = logging.getLogger(__name__) # Initialize logger

# --- Views for Referral Management ---

# referral/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt # REMINDER: Remove this in production!
from django.db import transaction
from django.utils import timezone
import uuid
import logging

from .models import Referral
from patients.models import Patient
from manage_hospital.models import Facility, Doctor

from manage_hospital.utils.sms import send_sms

logger = logging.getLogger(__name__)

@csrf_exempt # REMINDER: Remove this in production and implement proper CSRF handling!
def add_referral(request):
    patients = Patient.objects.all()
    # Only get approved facilities for selection
    hospitals = Facility.objects.filter(is_approved='Approved')
    # All doctors initially, to be filtered by AJAX
    doctors = Doctor.objects.all()

    if request.method == 'POST':
        # Get data from the form
        patient_id = request.POST.get('patient')
        referring_hospital_id = request.POST.get('referring_hospital')
        referring_doctor_id = request.POST.get('referring_doctor')
        receiving_hospital_id = request.POST.get('receiving_hospital')
        receiving_doctor_id = request.POST.get('receiving_doctor')
        status = request.POST.get('status', 'Requested') # Default to Requested
        main_reason = request.POST.get('main_reason')
        priority = request.POST.get('priority')
        referral_code = request.POST.get('referral_code')
        start_datetime_str = request.POST.get('start_datetime')
        end_datetime_str = request.POST.get('end_datetime')
        additional_notes = request.POST.get('additional_notes')

        try:
            # Validate and fetch related objects
            patient = get_object_or_404(Patient, id=patient_id)
            referring_hospital = get_object_or_404(Facility, id=referring_hospital_id)
            referring_doctor = get_object_or_404(Doctor, id=referring_doctor_id, hospital=referring_hospital)
            receiving_hospital = get_object_or_404(Facility, id=receiving_hospital_id)
            receiving_doctor = get_object_or_404(Doctor, id=receiving_doctor_id, hospital=receiving_hospital)

            # --- NEW VALIDATIONS ---
            # 1. Referring and Receiving Hospitals must not be the same
            if referring_hospital.id == receiving_hospital.id:
                messages.error(request, "Referring Hospital and Receiving Hospital cannot be the same.")
                # Important: If validation fails, render the form again with context
                random_code = f"REF-{str(uuid.uuid4())[:8].upper()}"
                context = {
                    'patients': Patient.objects.all(),
                    'hospitals': Facility.objects.filter(is_approved='Approved'),
                    'doctors': Doctor.objects.all(),
                    'random_code': random_code,
                    # Optionally, repopulate form fields from request.POST
                    'selected_patient': patient_id,
                    'selected_referring_hospital': referring_hospital_id,
                    'selected_referring_doctor': referring_doctor_id,
                    'selected_receiving_hospital': receiving_hospital_id,
                    'selected_receiving_doctor': receiving_doctor_id,
                    'selected_status': status,
                    'selected_main_reason': main_reason,
                    'selected_priority': priority,
                    'selected_start_datetime': start_datetime_str,
                    'selected_end_datetime': end_datetime_str,
                    'selected_additional_notes': additional_notes,
                }
                return render(request, 'referrals/add_referral.html', context)


            # 2. Referring and Receiving Doctors must not be the same
            if referring_doctor.id == receiving_doctor.id:
                messages.error(request, "Referring Doctor and Receiving Doctor cannot be the same.")
                # Render form again with context
                random_code = f"REF-{str(uuid.uuid4())[:8].upper()}"
                context = {
                    'patients': Patient.objects.all(),
                    'hospitals': Facility.objects.filter(is_approved='Approved'),
                    'doctors': Doctor.objects.all(),
                    'random_code': random_code,
                    'selected_patient': patient_id,
                    'selected_referring_hospital': referring_hospital_id,
                    'selected_referring_doctor': referring_doctor_id,
                    'selected_receiving_hospital': receiving_hospital_id,
                    'selected_receiving_doctor': receiving_doctor_id,
                    'selected_status': status,
                    'selected_main_reason': main_reason,
                    'selected_priority': priority,
                    'selected_start_datetime': start_datetime_str,
                    'selected_end_datetime': end_datetime_str,
                    'selected_additional_notes': additional_notes,
                }
                return render(request, 'referrals/add_referral.html', context)


            # 3. Check for active referrals for the patient
            # Define "active" as anything not 'Completed' or 'Rejected'
            active_referrals = Referral.objects.filter(
                patient=patient,
                status__in=['Requested', 'Approved', 'In Transit'] # Add other non-final statuses if any
            ).exists()

            if active_referrals:
                messages.error(request, f"The selected patient, {patient.full_name}, currently has an active referral ongoing. Please complete or reject the existing referral before creating a new one.")
                # Render form again with context
                random_code = f"REF-{str(uuid.uuid4())[:8].upper()}"
                context = {
                    'patients': Patient.objects.all(),
                    'hospitals': Facility.objects.filter(is_approved='Approved'),
                    'doctors': Doctor.objects.all(),
                    'random_code': random_code,
                    'selected_patient': patient_id,
                    'selected_referring_hospital': referring_hospital_id,
                    'selected_referring_doctor': referring_doctor_id,
                    'selected_receiving_hospital': receiving_hospital_id,
                    'selected_receiving_doctor': receiving_doctor_id,
                    'selected_status': status,
                    'selected_main_reason': main_reason,
                    'selected_priority': priority,
                    'selected_start_datetime': start_datetime_str,
                    'selected_end_datetime': end_datetime_str,
                    'selected_additional_notes': additional_notes,
                }
                return render(request, 'referrals/add_referral.html', context)
            # --- END NEW VALIDATIONS ---

            # Convert datetime strings to datetime objects
            start_datetime = timezone.make_aware(timezone.datetime.fromisoformat(start_datetime_str))
            end_datetime = timezone.make_aware(timezone.datetime.fromisoformat(end_datetime_str)) if end_datetime_str else None

            # Ensure referral code is unique before proceeding
            if Referral.objects.filter(referral_code=referral_code).exists():
                referral_code = f"REF-{str(uuid.uuid4())[:8].upper()}" # Regenerate if collision happens
                messages.warning(request, "Referral code collision detected. A new unique code was generated. Please review.")

            with transaction.atomic():
                # 1. Create the Referral record
                referral = Referral.objects.create(
                    patient=patient,
                    referring_hospital=referring_hospital,
                    referring_doctor=referring_doctor,
                    receiving_hospital=receiving_hospital,
                    receiving_doctor=receiving_doctor,
                    referral_code=referral_code,
                    status=status,
                    main_reason=main_reason,
                    priority=priority,
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    additional_notes=additional_notes
                )

                # 2. Prepare SMS messages
                patient_sms_message = (
                    f"Hello {patient.full_name}, you have a new medical referral. Your unique code is: "
                    f"{referral.referral_code}. Go to the rwanda health connect site, login page, click on the sidebar toggle button. select the Track patient referral info button"
                    f" Than entered your unique referral code to track your referral"
                )
                receiving_doctor_sms_message = (
                    f"Dr. {receiving_doctor.full_name}, you've received a new referral for {patient.full_name} "
                    f"(Code: {referral.referral_code}). Main reason: {referral.main_reason[:50]}... "
                    "  Go to the rwanda health connect site, login page, click on the sidebar toggle button. Select the Track patient referral info button"
                    f" Than entered the patient unique referral code to track their referral."

                )
                receiving_hospital_admin_sms_message = (
                    f"Dear {receiving_hospital.name} Admin, a new referral request has been made for "
                    f"{patient.full_name} (Code: {referral.referral_code}). "
                    "Login to manage this new referral."
                )
                requesting_hospital_admin_sms_message = (
                    f"Dear {referring_hospital.name} Admin, your referral request for {patient.full_name} "
                    f"(Code: {referral.referral_code}) has been successfully sent. "
                    "You will be notified when the status changes."
                )

                # 3. Send SMS messages
                try:
                    send_sms(patient.phone_number, patient_sms_message)
                    send_sms(receiving_doctor.phone_number, receiving_doctor_sms_message)
                    send_sms(receiving_hospital.admin_phone, receiving_hospital_admin_sms_message)
                    send_sms(referring_hospital.admin_phone, requesting_hospital_admin_sms_message)
                except Exception as sms_e:
                    messages.warning(request, f"Referral created, but SMS notifications failed: {sms_e}")
                    logger.error(f"SMS sending failed for referral {referral.referral_code}: {sms_e}")

                messages.success(request, f"Referral {referral.referral_code} added and notifications sent successfully!")
                return redirect('manage_referral')

        except Patient.DoesNotExist:
            messages.error(request, "Selected patient not found.")
        except Facility.DoesNotExist:
            messages.error(request, "One of the selected hospitals not found. Ensure facility is approved.")
        except Doctor.DoesNotExist:
            messages.error(request, "One of the selected doctors not found or not associated with the correct hospital.")
        except ValueError as e:
            messages.error(request, f"Invalid data provided: {e}")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during referral creation: {e}")
            import traceback
            traceback.print_exc()

    # For GET requests (or if POST fails validation and renders the page again)
    random_code = f"REF-{str(uuid.uuid4())[:8].upper()}"

    context = {
        'patients': patients,
        'hospitals': hospitals,
        'doctors': doctors, # All doctors initially, filtered by JS
        'random_code': random_code,
        # These are added to re-populate the form if a validation error occurs
        'selected_patient': request.POST.get('patient') if request.method == 'POST' else '',
        'selected_referring_hospital': request.POST.get('referring_hospital') if request.method == 'POST' else '',
        'selected_referring_doctor': request.POST.get('referring_doctor') if request.method == 'POST' else '',
        'selected_receiving_hospital': request.POST.get('receiving_hospital') if request.method == 'POST' else '',
        'selected_receiving_doctor': request.POST.get('receiving_doctor') if request.method == 'POST' else '',
        'selected_status': request.POST.get('status', 'Requested') if request.method == 'POST' else 'Requested',
        'selected_main_reason': request.POST.get('main_reason') if request.method == 'POST' else '',
        'selected_priority': request.POST.get('priority') if request.method == 'POST' else '',
        'selected_start_datetime': request.POST.get('start_datetime') if request.method == 'POST' else '',
        'selected_end_datetime': request.POST.get('end_datetime') if request.method == 'POST' else '',
        'selected_additional_notes': request.POST.get('additional_notes') if request.method == 'POST' else '',
    }
    return render(request, 'referrals/add_referral.html', context)

# --- AJAX Views ---
@require_GET
def get_hospital_and_doctors_for_patient(request):
    patient_id = request.GET.get('patient_id')
    if not patient_id:
        return JsonResponse({'error': 'Patient ID is required'}, status=400)

    try:
        # Crucial: Ensure patient.current_hospital is populated if it exists
        patient = Patient.objects.select_related('current_hospital').get(id=patient_id)
        referring_hospital_data = None
        referring_doctors_data = []

        if patient.current_hospital: # This checks if the patient actually has a current_hospital
            referring_hospital_data = {
                'id': patient.current_hospital.id,
                'name': patient.current_hospital.name
            }
            # Fetch doctors associated with the patient's current hospital
            referring_doctors = Doctor.objects.filter(hospital=patient.current_hospital)
            referring_doctors_data = [{'id': doc.id, 'full_name': doc.full_name} for doc in referring_doctors]

        return JsonResponse({
            'referring_hospital': referring_hospital_data,
            'referring_doctors': referring_doctors_data
        })
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_hospital_and_doctors_for_patient: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_doctors_for_hospital(request):
    hospital_id = request.GET.get('hospital_id')
    if not hospital_id:
        return JsonResponse({'error': 'Hospital ID is required'}, status=400)

    try:
        doctors = Doctor.objects.filter(hospital_id=hospital_id)
        doctors_data = [{'id': doc.id, 'full_name': doc.full_name} for doc in doctors]
        return JsonResponse({'doctors': doctors_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --- Placeholder Views for Other Referral Pages (Updated referral_details) ---
# referral/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
import uuid
import logging

from .models import Referral
from patients.models import Patient
from manage_hospital.models import Facility, Doctor

from manage_hospital.utils.sms import send_sms

logger = logging.getLogger(__name__)

# --- MODIFIED: manage_referral view ---
def manage_referral(request):
    referrals_queryset = Referral.objects.select_related(
        'patient',
        'referring_hospital',
        'referring_doctor',
        'receiving_hospital',
        'receiving_doctor'
    ).all().order_by('-created_at')

    referrals_for_template = [] # List to hold Referral objects with added properties for template
    referrals_data_for_js = []  # List to hold dictionaries for JSON

    for referral in referrals_queryset:
        # Prepare data for template display
        referral.status_css = referral.status.lower().replace(' ', '-')
        referral.priority_css = referral.priority.lower().replace(' ', '-')
        referrals_for_template.append(referral)

        # Prepare data for JavaScript JSON
        referrals_data_for_js.append({
            'id': str(referral.id),
            'patient': {'id': str(referral.patient.id), 'full_name': referral.patient.full_name},
            'referring_hospital': {'id': str(referral.referring_hospital.id), 'name': referral.referring_hospital.name},
            'referring_doctor': {'id': str(referral.referring_doctor.id), 'full_name': f"Dr. {referral.referring_doctor.full_name}"},
            'receiving_hospital': {'id': str(referral.receiving_hospital.id), 'name': referral.receiving_hospital.name},
            'receiving_doctor': {'id': str(referral.receiving_doctor.id), 'full_name': f"Dr. {referral.receiving_doctor.full_name}"},
            'status': referral.status,
            'status_css': referral.status.lower().replace(' ', '-'), # Add formatted status for JS
            'start_datetime': referral.start_datetime.isoformat() if referral.start_datetime else '',
            'end_datetime': referral.end_datetime.isoformat() if referral.end_datetime else '',
            'main_reason': referral.main_reason,
            'priority': referral.priority,
            'priority_css': referral.priority.lower().replace(' ', '-'), # Add formatted priority for JS
            'referral_code': referral.referral_code,
            'additional_notes': referral.additional_notes,
            'created_at': referral.created_at.isoformat() if referral.created_at else '',
        })

    patients = Patient.objects.all().order_by('full_name')
    hospitals = Facility.objects.filter(is_approved='Approved').order_by('name')
    doctors = Doctor.objects.all().order_by('full_name')

    context = {
        'referrals': referrals_for_template, # Use the list with added properties
        'referrals_json': JsonResponse(referrals_data_for_js, safe=False).content.decode('utf-8'),
        'patients': patients,
        'hospitals': hospitals,
        'doctors': doctors,
    }
    return render(request, 'referrals/manage_referral.html', context)

# In your `referral/views.py`

from datetime import datetime # <--- ENSURE THIS IS THE ONLY datetime import for the class
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
import uuid
import logging

# Import your models (ensure all are here if used in this view)
from .models import Referral
from patients.models import Patient
from manage_hospital.models import Facility, Doctor

# Ensure this path is correct for your SMS utility
from manage_hospital.utils.sms import send_sms

logger = logging.getLogger(__name__)

from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt # REMINDER: Remove this in production!
from django.db import transaction
from django.utils import timezone
import uuid
import logging

# Import your existing models
from .models import Referral
from patients.models import Patient
from manage_hospital.models import Facility, Doctor

# Ensure this path is correct for your SMS utility
from manage_hospital.utils.sms import send_sms

logger = logging.getLogger(__name__)

@require_POST
@csrf_exempt # REMINDER: Remove this in production and implement proper CSRF handling!
def referral_update_view(request, pk):
    try:
        referral = get_object_or_404(Referral, id=pk)

        # --- NEW VALIDATION: Prevent editing if status is 'Completed' ---
        if referral.status == 'Completed':
            error_message = f"Referral {referral.referral_code} cannot be updated because its status is 'Completed'."
            logger.warning(error_message)
            return JsonResponse({'success': False, 'error': error_message}, status=403) # 403 Forbidden

        # Store old values for comparison, especially old_status
        old_status = referral.status
        old_main_reason = referral.main_reason
        old_priority = referral.priority
        old_additional_notes = referral.additional_notes

        # Update referral fields from request.POST
        referral.status = request.POST.get('status', referral.status)
        referral.main_reason = request.POST.get('main_reason', referral.main_reason)
        referral.priority = request.POST.get('priority', referral.priority)
        referral.additional_notes = request.POST.get('additional_notes', referral.additional_notes)

        # Handle start_datetime
        start_datetime_str = request.POST.get('start_datetime')
        if start_datetime_str:
            try:
                naive_dt = datetime.fromisoformat(start_datetime_str)
                referral.start_datetime = timezone.make_aware(naive_dt)
            except ValueError:
                logger.error(f"Invalid start_datetime format for referral {pk}: {start_datetime_str}", exc_info=True)
                return JsonResponse({'success': False, 'error': 'Invalid format for Start Date/Time.'}, status=400)
        else:
            logger.warning(f"Start Date/Time missing for referral {pk} update.")
            return JsonResponse({'success': False, 'error': 'Start Date/Time is required.'}, status=400)

        # Handle end_datetime
        end_datetime_str = request.POST.get('end_datetime')
        if end_datetime_str:
            try:
                naive_dt = datetime.fromisoformat(end_datetime_str)
                referral.end_datetime = timezone.make_aware(naive_dt)
            except ValueError:
                logger.error(f"Invalid end_datetime format for referral {pk}: {end_datetime_str}", exc_info=True)
                return JsonResponse({'success': False, 'error': 'Invalid format for End Date/Time.'}, status=400)
        else:
            referral.end_datetime = None

        referral.full_clean() # Perform full model validation
        referral.save() # Save the updated referral details

        logger.info(f"Referral {pk} updated successfully by user {request.user if request.user.is_authenticated else 'Anonymous'}.")

        # --- Update Patient's current_hospital if status becomes 'Completed' ---
        # This block executes after the referral itself has been successfully saved.
        if old_status != 'Completed' and referral.status == 'Completed':
            logger.info(f"Referral {referral.referral_code} status changed to 'Completed'. Attempting to update patient's current hospital.")
            try:
                patient_instance = referral.patient # Get the Patient object linked to this referral
                receiving_hospital_instance = referral.receiving_hospital # Get the Receiving Hospital linked to this referral

                if patient_instance and receiving_hospital_instance:
                    logger.debug(f"Updating patient {patient_instance.full_name} (ID: {patient_instance.id}) current hospital from {patient_instance.current_hospital.name if patient_instance.current_hospital else 'None'} to {receiving_hospital_instance.name}.")
                    patient_instance.current_hospital = receiving_hospital_instance
                    patient_instance.save() # Crucial: Save the changes to the Patient model
                    logger.info(f"Patient {patient_instance.full_name}'s current hospital successfully updated to {receiving_hospital_instance.name}.")
                    messages.info(request, f"Patient {patient_instance.full_name}'s current hospital has been updated to {receiving_hospital_instance.name}.")
                else:
                    logger.warning(f"Patient or Receiving Hospital object was None for referral {pk} during 'Completed' status update attempt. Patient update skipped.")
            except Exception as patient_update_error:
                logger.error(f"Error updating patient's current hospital for referral {pk}: {patient_update_error}", exc_info=True)
                messages.error(request, f"Failed to update patient's current hospital: {patient_update_error}")
        else:
            logger.info(f"Referral {referral.referral_code} status did not change to 'Completed', or was already 'Completed'. Patient's current hospital not updated.")

        # --- SMS Notification Logic ---
        # Only send notifications if there were actual changes to "important" fields
        if (old_status != referral.status or
            old_main_reason != referral.main_reason or
            old_priority != referral.priority or
            old_additional_notes != referral.additional_notes):

            patient = referral.patient
            referring_hospital = referral.referring_hospital
            referring_doctor = referral.referring_doctor
            receiving_hospital = referral.receiving_hospital
            receiving_doctor = referral.receiving_doctor

            update_message_base = (
                f"Referral Update: The referral for patient {patient.full_name} "
                f"(Code: {referral.referral_code}) has been updated. "
                f"New Status: {referral.status}. "
                f"Main Reason: {referral.main_reason[:70]}..."
            )

            try:
                # Notify Patient
                send_sms(patient.phone_number, f"Hello {patient.full_name}, {update_message_base} Please check your referral tracking page.")

                # Notify Referring Doctor
                send_sms(referring_doctor.phone_number, f"Dr. {referring_doctor.full_name}, {update_message_base}")

                # Notify Referring Hospital Admin
                send_sms(referring_hospital.admin_phone, f"{referring_hospital.name} Admin, {update_message_base}")

                # Notify Receiving Doctor
                send_sms(receiving_doctor.phone_number, f"Dr. {receiving_doctor.full_name}, {update_message_base}")

                # Notify Receiving Hospital Admin
                send_sms(receiving_hospital.admin_phone, f"{receiving_hospital.name} Admin, {update_message_base}")

            except Exception as sms_e:
                logger.error(f"SMS sending failed after referral update {referral.referral_code}: {sms_e}", exc_info=True)
                messages.warning(request, f"Referral updated, but some notifications failed: {sms_e}")

        return JsonResponse({'success': True, 'message': 'Referral updated successfully!'})

    except Exception as e:
        logger.error(f"Unhandled error updating referral {pk}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': f"An unexpected error occurred: {e}"}, status=400)
@require_POST
def referral_delete_view(request, pk):
    try:
        # Get the referral object, or return a 404 if not found
        referral = get_object_or_404(Referral, pk=pk) # Make sure 'Referral' model is imported
        referral.delete()
        # On successful deletion, return a JSON response indicating success
        return JsonResponse({'success': True, 'message': 'Referral deleted successfully!'})
    except Referral.DoesNotExist:
        # If the referral wasn't found, return a 404 JSON response
        return JsonResponse({'success': False, 'error': 'Referral not found.'}, status=404)
    except Exception as e:
        # Handle any other exceptions during deletion (e.g., database error)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
def track_referral(request):
    # Logic to allow users to track a referral using its code
    return render(request, 'referrals/track_referral.html')

# MODIFIED: This view now expects referral_code as a GET parameter
def referral_details(request):
    referral_code = request.GET.get('referral_code')

    if not referral_code:
        return JsonResponse({'error': 'Referral code not provided'}, status=400)

    try:
        referral = get_object_or_404(Referral, referral_code=referral_code)
        print(f"Found referral: {referral}")  # Debug print
        
        # Prepare the response data
        data = {
            'patient': {
                'full_name': referral.patient.full_name,
                'date_of_birth': referral.patient.date_of_birth.strftime('%d/%m/%Y'),
                'address': referral.patient.current_address,
                'phone': referral.patient.phone_number,
                'email': referral.patient.email,
                'emergency_contact': referral.patient.emergency_contact_number,
                'gender': referral.patient.gender,
                'nationality': referral.patient.nationality,
                'marital_status': referral.patient.marital_status,
                'occupation': referral.patient.occupation,
                'status': referral.patient.current_status,
                'hospital': referral.patient.current_hospital.name if referral.patient.current_hospital else '',
                'blood_group': referral.patient.blood_group,
                'genotype': referral.patient.genotype,
                'allergies': referral.patient.medical_records.first().allergies if referral.patient.medical_records.exists() else '',
                'chronic_conditions': referral.patient.medical_records.first().chronic_condition if referral.patient.medical_records.exists() else '',
                'image': referral.patient.image.url if referral.patient.image else ''
            },
            'referring_doctor': {
                'full_name': referral.referring_doctor.full_name,
                'date_of_birth': referral.referring_doctor.date_of_birth.strftime('%d/%m/%Y') if referral.referring_doctor.date_of_birth else '',
                'gender': referral.referring_doctor.gender,
                'nationality': referral.referring_doctor.nationality,
                'phone': referral.referring_doctor.phone_number,
                'address': referral.referring_doctor.address,
                'email': referral.referring_doctor.email,
                'specialty': referral.referring_doctor.specialty,
                'hospital': referral.referring_doctor.hospital.name if referral.referring_doctor.hospital else '',
                'license': referral.referring_doctor.license_number
            },
            'referring_hospital': {
                'name': referral.referring_hospital.name,
                'facility_type': referral.referring_hospital.facility_type,
                'facility_level': referral.referring_hospital.facility_level,
                'address': referral.referring_hospital.address,
                'province': referral.referring_hospital.province,
                'district': referral.referring_hospital.district,
                'sector': referral.referring_hospital.sector,
                'cell': referral.referring_hospital.cell,
                'village': referral.referring_hospital.village,
                'contact': referral.referring_hospital.admin_phone,
                'email': referral.referring_hospital.admin_email
            },
            'receiving_doctor': {
                'full_name': referral.receiving_doctor.full_name,
                'date_of_birth': referral.receiving_doctor.date_of_birth.strftime('%d/%m/%Y') if referral.receiving_doctor.date_of_birth else '',
                'gender': referral.receiving_doctor.gender,
                'nationality': referral.receiving_doctor.nationality,
                'phone': referral.receiving_doctor.phone_number,
                'address': referral.receiving_doctor.address,
                'email': referral.receiving_doctor.email,
                'specialty': referral.receiving_doctor.specialty,
                'hospital': referral.receiving_doctor.hospital.name if referral.receiving_doctor.hospital else '',
                'license': referral.receiving_doctor.license_number
            },
            'receiving_hospital': {
                'name': referral.receiving_hospital.name,
                'facility_type': referral.receiving_hospital.facility_type,
                'facility_level': referral.receiving_hospital.facility_level,
                'address': referral.receiving_hospital.address,
                'province': referral.receiving_hospital.province,
                'district': referral.receiving_hospital.district,
                'sector': referral.receiving_hospital.sector,
                'cell': referral.receiving_hospital.cell,
                'village': referral.receiving_hospital.village,
                'contact': referral.receiving_hospital.admin_phone,
                'email': referral.receiving_hospital.admin_email
            },
            'referral': {
                'status': referral.status,
                'priority': referral.priority,
                'start_datetime': referral.start_datetime.strftime('%d/%m/%Y %I:%M %p'),
                'end_datetime': referral.end_datetime.strftime('%d/%m/%Y %I:%M %p') if referral.end_datetime else None,
                'main_reason': referral.main_reason,
                'additional_notes': referral.additional_notes,
                'created_at': referral.created_at.strftime('%d/%m/%Y %I:%M %p')
            }
        }
        
        print(f"Returning data: {data}")  # Debug print
        return JsonResponse(data)
    except Referral.DoesNotExist:
        print(f"Referral not found for code: {referral_code}")  # Debug print
        return JsonResponse({'error': f"Referral with code '{referral_code}' not found."}, status=404)
    except Exception as e:
        print(f"Error processing referral: {str(e)}")  # Debug print
        return JsonResponse({'error': str(e)}, status=500)

def referral_list(request):
    referrals = Referral.objects.all().order_by('-created_at')
    context = {
        'referrals': referrals
    }
    return render(request, 'referrals/referral_list.html', context)

def patients_referrals(request):
    # Logic to show referrals specific to the logged-in patient or hospital
    # This might require checking request.user and filtering accordingly
    return render(request, 'referrals/patients_referral.html')