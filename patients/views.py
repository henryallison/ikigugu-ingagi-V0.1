# patients/views.py
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import PatientForm
from .models import Patient, MedicalRecord
from accounts.models import Facility # Adjust this import path if Facility is in a different app
import cloudinary.uploader
from django.conf import settings
from manage_hospital.utils.sms import send_sms
from django.http import JsonResponse # Import JsonResponse for AJAX responses
from django.views.decorators.http import require_POST # For enforcing POST requests
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# ... (your existing views: add_patient, manage_patients) ...

import cloudinary.uploader  # Ensure this is imported at the top of your views.py


@require_POST  # Ensures that only POST requests are accepted for this view
def delete_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    try:
        # Delete image from Cloudinary if a cloudinary_url exists for the patient
        if patient.cloudinary_url:
            # Extract public_id from Cloudinary URL
            # Example URL structure: https://res.cloudinary.com/your_cloud_name/image/upload/v12345/folder/public_id.jpg
            # We want 'folder/public_id' or just 'public_id' if no folder
            # A robust way is to split by '/' and take the last part before the extension
            try:
                # Assuming the public_id is the last segment before the file extension
                # e.g., 'patient_images/abc123def' or 'profile_pics/xyz456'
                # If your public_id includes folders, the split will typically capture that.
                # A more robust way to get the public_id from a Cloudinary URL
                # that includes 'upload/' but not 'vYYYY/':
                url_parts = patient.cloudinary_url.split('/upload/')
                if len(url_parts) > 1:
                    # Get the part after '/upload/' which contains version and public_id/filename
                    path_after_upload = url_parts[1]
                    # Remove any version string (e.g., 'v12345/') if present
                    if path_after_upload.startswith('v') and '/' in path_after_upload:
                        path_after_upload = path_after_upload.split('/', 1)[1]  # remove vXXXXX/

                    # Remove file extension
                    public_id = path_after_upload.rsplit('.', 1)[0]

                    print(f"Attempting to delete Cloudinary image with public_id: {public_id}")
                    # Perform the deletion
                    deletion_result = cloudinary.uploader.destroy(public_id)
                    print(f"Cloudinary deletion result for {public_id}: {deletion_result}")
                    if deletion_result.get('result') != 'ok':
                        # Log if Cloudinary reports an issue but don't stop patient deletion
                        print(f"Warning: Cloudinary deletion not 'ok' for {public_id}: {deletion_result}")
                else:
                    print(f"Warning: Could not parse Cloudinary URL for public_id: {patient.cloudinary_url}")

            except Exception as cloudinary_e:
                print(f"Error during Cloudinary image deletion for {patient.cloudinary_url}: {cloudinary_e}")
                # Don't re-raise, allow patient deletion to proceed

        patient.delete()  # Delete the patient record from the database
        messages.success(request, f"Patient '{patient.full_name}' deleted successfully.")
        return JsonResponse({'status': 'success', 'message': 'Patient deleted successfully.'})
    except Exception as e:
        messages.error(request, f"Error deleting patient '{patient.full_name}': {e}")
        # Return a 500 status code for server-side errors
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# The modified edit_patient view for AJAX handling
@require_POST # Ensure this view only accepts POST requests for updates
def edit_patient(request, pk):
    try:
        patient = get_object_or_404(Patient, pk=pk)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Patient not found.', 'errors': {'detail': str(e)}}, status=404)

    # Note: We're only handling POST requests for the actual edit logic here,
    # as the GET request to populate the edit modal is handled client-side
    # by reading from the table or another AJAX endpoint.
    form = PatientForm(request.POST, request.FILES, instance=patient)

    if form.is_valid():
        try:
            edited_patient = form.save(commit=False)

            # Handle image update logic:
            # If a new image file is uploaded, update cloudinary_url.
            if 'image' in request.FILES:
                upload_result = cloudinary.uploader.upload(
                    request.FILES['image'],
                    upload_preset=settings.CLOUDINARY_UPLOAD_PRESET
                )
                edited_patient.cloudinary_url = upload_result['secure_url']
            # If no new image is uploaded, but there was an existing one,
            # and the form's logic (PatientForm's clean_image method) allows
            # clearing the image if not required or explicitly cleared,
            # this would be handled by the form.
            # If the image is ALWAYS required, form.is_valid() should ensure it's present.
            elif not edited_patient.cloudinary_url: # If no new image and no existing image (should be caught by form if required)
                 # This scenario implies the image is required but missing after update.
                 # The form.is_valid() should ideally prevent this if the field is truly required.
                 pass


            edited_patient.save()

            message_sms = f"Dear, {edited_patient.full_name}, your personal records was just updated within the Rwanda Health Connect Referral System."
            sms_result = send_sms(edited_patient.phone_number, message_sms)
            print(f"SMS Result (Edit): {sms_result}")

            # Return JSON success response for AJAX
            if sms_result and sms_result.get('status') == 'success':
                return JsonResponse({
                    'status': 'success',
                    'message': f"Patient {edited_patient.full_name}'s record updated successfully and SMS notification sent!",
                    'patient_id': edited_patient.pk
                })
            else:
                return JsonResponse({
                    'status': 'success', # Still a success from the data update perspective
                    'message': f"Patient {edited_patient.full_name}'s record updated successfully. SMS notification failed, but record is saved.",
                    'patient_id': edited_patient.pk
                })

        except Exception as e:
            # Catch any other unexpected errors during save/SMS
            print(f"Error during patient save/SMS: {e}")
            return JsonResponse({'status': 'error', 'message': f'Server error during update: {e}', 'errors': {'detail': str(e)}}, status=500)
    else:
        # If form is NOT valid, return JSON with errors
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = [str(error) for error_list in error_list for error in error_list] # Iterate over lists of errors per field
        print(f"Form validation errors for edit_patient: {errors}")
        return JsonResponse({'status': 'error', 'message': 'Validation failed. Please correct the form errors.', 'errors': errors}, status=400) # 400 Bad Request for client-side validation errors

# Modified manage_patients view to pass approved_hospitals
def manage_patients(request):
    patients = Patient.objects.all().order_by('full_name')
    # --- MODIFICATION START ---
    # Removed: , facility_type__iexact='hospital'
    approved_hospitals = Facility.objects.filter(is_approved='Approved')
    # --- MODIFICATION END ---
    context = {
        'patients': patients,
        'approved_hospitals': approved_hospitals,
    }
    return render(request, 'patients/manage_patients.html', context)



def add_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)

            if patient.image:
                upload_result = cloudinary.uploader.upload(
                    patient.image,
                    upload_preset=settings.CLOUDINARY_UPLOAD_PRESET
                )
                patient.cloudinary_url = upload_result['secure_url']
            patient.save()

            message_sms = f"Welcome, {patient.full_name}! You've been successfully registered with Rwanda Health Connect. We're here to serve your healthcare needs."
            sms_result = send_sms(patient.phone_number, message_sms)
            print(f"SMS Result: {sms_result}")

            # IMPORTANT: Add the message to the session before redirecting
            if sms_result and sms_result.get('status') == 'success':
                messages.success(request, f"Patient {patient.full_name} added successfully and welcome SMS sent!")
            else:
                messages.success(request, f"Patient {patient.full_name} added successfully. SMS sending failed, but patient record is saved.")

            # Redirect to the manage_patients page
            return redirect('patients:manage_patients')
        else:
            # If form is invalid, re-render add_patients.html with errors
            pass # Form errors will be handled in the template

    else:
        form = PatientForm()

    # MODIFICATION: The line below has been changed to remove the facility_type filter.
    approved_hospitals = Facility.objects.filter(is_approved='Approved')

    context = {
        'form': form,
        'approved_hospitals': approved_hospitals,
    }
    # This render is for GET requests or invalid POSTs; it won't have the success message
    return render(request, 'patients/add_patients.html', context)
def medical_records(request):
    # Get all medical records with related patient and hospital data
    medical_records_qs = MedicalRecord.objects.select_related('patient', 'current_hospital').all()

    # Prepare data for JavaScript, ensuring full text fields are included
    medical_records_data = []
    for record in medical_records_qs:
        medical_records_data.append({
            'id': record.id,
            'patient': {
                'id': record.patient.id,
                'full_name': record.patient.full_name
            },
            'current_hospital': {
                'id': record.current_hospital.id if record.current_hospital else None,
                'name': record.current_hospital.name if record.current_hospital else 'N/A'
            },
            'primary_diagnosis': record.primary_diagnosis, # FULL TEXT
            'chronic_condition': record.chronic_condition, # FULL TEXT
            'allergies': record.allergies,                 # FULL TEXT
            'past_surgeries': record.past_surgeries,       # FULL TEXT
            'current_medication': record.current_medication, # FULL TEXT
            'created_at': record.created_at.strftime("%Y-%m-%d %H:%M") # Format as string
        })

    context = {
        'medical_records': medical_records_qs, # This is for your Django template loop (table display)
        'medical_records_json': json.dumps(medical_records_data) # This is for your JavaScript (modal display)
    }
    return render(request, 'patients/medical_records.html', context)

def add_records(request):
    if request.method == 'GET':
        # Get approved hospitals
        approved_hospitals = Facility.objects.filter(is_approved='Approved', facility_type__iexact='hospital')
        # Get all registered patients
        patients = Patient.objects.all()
        
        context = {
            'approved_hospitals': approved_hospitals,
            'patients': patients
        }
        return render(request, 'patients/add_records.html', context)

    elif request.method == 'POST':
        # Handle form submission
        patient_id = request.POST.get('patient')
        hospital_id = request.POST.get('current_hospital')
        primary_diagnosis = request.POST.get('primary_diagnosis')
        chronic_condition = request.POST.get('chronic_condition')
        allergies = request.POST.get('allergies')
        past_surgeries = request.POST.get('past_surgeries')
        current_medication = request.POST.get('current_medication')
        
        try:
            # First check if patient already has a medical record
            if MedicalRecord.objects.filter(patient_id=patient_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This patient already has a medical record. Please edit the existing record instead.'
                }, status=400)

            patient = Patient.objects.get(id=patient_id)
            
            # Check if patient is registered with a hospital
            if patient.current_hospital:
                # If patient is registered with a hospital, use that hospital
                current_hospital = patient.current_hospital
            else:
                # If patient is not registered, use the selected hospital
                current_hospital = Facility.objects.get(id=hospital_id)
            
            medical_record = MedicalRecord.objects.create(
                patient=patient,
                current_hospital=current_hospital,
                primary_diagnosis=primary_diagnosis,
                chronic_condition=chronic_condition,
                allergies=allergies,
                past_surgeries=past_surgeries,
                current_medication=current_medication
            )
            
            return JsonResponse({'success': True, 'message': 'Medical record created successfully'})
            
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Patient not found'}, status=400)
        except Facility.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Hospital not found'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
def delete_record(request, record_id):
    if request.method == 'DELETE':
        try:
            record = get_object_or_404(MedicalRecord, id=record_id)
            record.delete()
            return JsonResponse({'success': True, 'message': 'Medical record deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def update_record(request, record_id):
    if request.method == 'POST':
        try:
            record = get_object_or_404(MedicalRecord, id=record_id)
            
            # Update fields from request.POST
            record.primary_diagnosis = request.POST.get('primary_diagnosis', '')
            record.chronic_condition = request.POST.get('chronic_condition', '')
            record.allergies = request.POST.get('allergies', '')
            record.past_surgeries = request.POST.get('past_surgeries', '')
            record.current_medication = request.POST.get('current_medication', '')
            
            # Update related objects if they exist
            if 'patient' in request.POST:
                patient_id = request.POST.get('patient')
                patient = get_object_or_404(Patient, id=patient_id)
                record.patient = patient
            
            if 'current_hospital' in request.POST:
                hospital_id = request.POST.get('current_hospital')
                hospital = get_object_or_404(Facility, id=hospital_id)
                record.current_hospital = hospital
            
            record.save()
            
            return JsonResponse({'success': True, 'message': 'Medical record updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def get_patient_hospitals(request):
    if request.method == 'GET':
        patient_id = request.GET.get('patient_id')
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # If patient has a registered hospital, return only that hospital
            if patient.current_hospital:
                hospitals = [patient.current_hospital]
            else:
                # If patient is not registered, return all approved hospitals
                hospitals = Facility.objects.filter(is_approved='Approved', facility_type__iexact='hospital')
            
            return JsonResponse({
                'success': True,
                'hospitals': [
                    {
                        'id': hospital.id,
                        'name': hospital.name
                    }
                    for hospital in hospitals
                ]
            })
            
        except Patient.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Patient not found'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
def get_hospital_patients(request):
    if request.method == 'GET':
        hospital_id = request.GET.get('hospital_id')
        try:
            # Get all patients registered at this hospital
            patients = Patient.objects.filter(current_hospital_id=hospital_id)
            return JsonResponse({
                'success': True,
                'patients': [
                    {
                        'id': patient.id,
                        'full_name': patient.full_name
                    }
                    for patient in patients
                ]
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
def check_existing_record(request):
    if request.method == 'GET':
        patient_id = request.GET.get('patient_id')
        try:
            exists = MedicalRecord.objects.filter(patient_id=patient_id).exists()
            return JsonResponse({
                'success': True,
                'exists': exists
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)