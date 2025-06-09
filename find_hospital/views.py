from django.http import JsonResponse
from django.shortcuts import render
from accounts.models import Facility
from manage_hospital.models import Doctor, HospitalInventory
import json
from django.views.decorators.http import require_GET

def find_hospital(request):
    # Get all approved facilities (hospitals)
    hospitals = Facility.objects.filter(is_approved='Approved')
    print(f"\n=== Debug Information ===")
    print(f"Number of approved hospitals found: {hospitals.count()}")

    # Prepare data for template
    hospital_data = []
    for hospital in hospitals:
        print(f"\nProcessing hospital: {hospital.name}")
        print(f"Hospital ID: {hospital.id}")

        # Get associated doctors
        doctors = hospital.doctors.all()
        print(f"Found {doctors.count()} doctors for {hospital.name}")

        # Get inventory if available
        inventory = HospitalInventory.objects.filter(hospital=hospital).first()
        inventory_text = None
        if inventory and inventory.inventory_list:
            print(f"Inventory found for {hospital.name}")
            print(f"Inventory content: {inventory.inventory_list}")
            inventory_text = inventory.inventory_list
        else:
            print(f"No inventory found for {hospital.name}")

        hospital_data.append({
            'id': str(hospital.id),
            'name': hospital.name,
            'facilityType': hospital.facility_type,
            'facilityLevel': hospital.facility_level,
            'address': hospital.address,
            'province': hospital.province,
            'district': hospital.district,
            'sector': hospital.sector,
            'cell': hospital.cell,
            'village': hospital.village,
            'admin': {
                'firstName': hospital.admin_first_name,
                'lastName': hospital.admin_last_name,
                'email': hospital.admin_email,
                'phone': hospital.admin_phone,
                'position': hospital.admin_position
            },
            'doctors': [
                {
                    'fullName': doctor.full_name,
                    'dateOfBirth': str(doctor.date_of_birth) if doctor.date_of_birth else '',
                    'gender': doctor.gender,
                    'nationality': doctor.nationality,
                    'phone': doctor.phone_number,
                    'address': doctor.address,
                    'email': doctor.email,
                    'specialty': doctor.specialty,
                    'hospital': hospital.name,
                    'license': doctor.license_number
                }
                for doctor in doctors
            ],
            'inventory': inventory_text,  # Now passing just the text directly
            'license_number': hospital.license_number,
            'is_approved': hospital.is_approved,
            'created_at': str(hospital.created_at),
            'updated_at': str(hospital.updated_at)
        })

    print(f"\nFinal hospital data to be passed to template:")
    for hosp in hospital_data:
        print(f"- Hospital: {hosp['name']}")
        print(f"  ID: {hosp['id']}")
        print(f"  Doctors: {len(hosp['doctors'])}")
        print(f"  Inventory: {'Exists' if hosp['inventory'] else 'None'}")

    # Convert to JSON string in the view
    hospitals_json = json.dumps(hospital_data)
    return render(request, 'find_hospital.html', {'hospitals': hospitals_json})


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
