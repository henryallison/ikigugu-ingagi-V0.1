# find_hospital/views.py
from django.shortcuts import render
from accounts.models import Facility
from manage_hospital.models import Doctor, HospitalInventory
import json

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
        print(f"Is approved: {hospital.is_approved}")
        
        # Get associated doctors
        doctors = hospital.doctors.all()
        print(f"Found {doctors.count()} doctors for {hospital.name}")
        
        # Get inventory if available
        inventory = HospitalInventory.objects.filter(hospital=hospital).first()
        print(f"Inventory query result for {hospital.name}: {inventory}")
        inventory_items = []
        if inventory:
            print(f"Inventory record found for {hospital.name}")
            print(f"Inventory list content: {inventory.inventory_list}")
            if inventory.inventory_list:
                # The inventory is stored as plain text in numbered format
                # Convert it to a structured list of items
                try:
                    # Split by newlines and process each line
                    lines = inventory.inventory_list.strip().split('\n')
                    for line in lines:
                        if line.strip():  # Skip empty lines
                            # Extract number and item description
                            parts = line.split(')')
                            if len(parts) == 2:
                                number = parts[0].strip()
                                description = parts[1].strip()
                                inventory_items.append({
                                    'number': number,
                                    'description': description
                                })
                    print(f"Successfully parsed {len(inventory_items)} inventory items")
                except Exception as e:
                    print(f"Error processing inventory text for {hospital.name}: {str(e)}")
                    print(f"Inventory content: {inventory.inventory_list}")
            else:
                print(f"No inventory_list field content for {hospital.name}")
        else:
            print(f"No inventory record found for {hospital.name}")
        
        hospital_data.append({
            'id': str(hospital.id),  # Convert to string to avoid JSON serialization issues
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
            'inventory': inventory_items,
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
        print(f"  Inventory items: {len(hosp['inventory'])}")
    
    # Convert to JSON string in the view
    hospitals_json = json.dumps(hospital_data)
    print(f"\nJSON data to be passed to template:")
    print(hospitals_json)
    
    return render(request, 'find_hospital.html', {'hospitals': hospitals_json})