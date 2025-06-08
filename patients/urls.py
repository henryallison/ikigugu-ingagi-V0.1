from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('edit/<int:pk>/', views.edit_patient, name='edit_patient'),
    # Changed <int:pk> to <uuid:pk> if your Patient ID is UUID
    path('delete/<int:pk>/', views.delete_patient, name='delete_patient'),  # NEW URL pattern for deletion
    path('manage_patients/', views.manage_patients, name='manage_patients'),
    path('add/', views.add_patient, name='add_patient'),
    path('medical_records/', views.medical_records, name='medical_records'),
    path('add_records/', views.add_records, name='add_records'),
    path('delete_record/<int:record_id>/', views.delete_record, name='delete_record'),
    path('update_record/<int:record_id>/', views.update_record, name='update_record'),
    path('get_patient_hospitals/', views.get_patient_hospitals, name='get_patient_hospitals'),
    path('get_hospital_patients/', views.get_hospital_patients, name='get_hospital_patients'),
    path('check_existing_record/', views.check_existing_record, name='check_existing_record'),
]