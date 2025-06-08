from django.urls import path, include
from manage_hospital.views import (
    request_credentials_email,  # Changed from request_credentials
    upload_documents,
    success_page,
    request_credentials_sms,
    edit_doctor_ajax,
    delete_doctor_ajax,
    manage_doctors,
    add_doctor,
    manage_hospital_inventory,
    edit_hospital_inventory,
    delete_hospital_inventory,

)
from . import views
from .views import download_hospital_credentials


urlpatterns = [
    path('get-approved-hospitals/', views.get_approved_hospitals, name='get_approved_hospitals'),
    path('delete_facility_documents/<int:facility_id>/', views.delete_facility_documents, name='delete_facility_documents'),
    # Main hospital management
    path('', views.manage_hospital_view, name='manage_hospital_home'),
    path('register/', views.manage_hospital_registration_view, name='manage_hospital_register'),
    path('add/', views.add_hospital_view, name='add_hospital'),
    path('manage_hospital_inventory/', views.manage_hospital_inventory, name='manage_hospital_inventory'),
    
    path('view_inventory/<int:inventory_id>/', views.view_hospital_inventory, name='view_hospital_inventory'),
    path('edit_inventory/<int:inventory_id>/', views.edit_hospital_inventory, name='edit_hospital_inventory'),
    path('delete_inventory/<int:inventory_id>/', views.delete_hospital_inventory, name='delete_hospital_inventory'),
    
    path('evaluate-credentials/', views.evaluate_hospital_credentials, name='evaluate_hospital_credentials'),
    path('manage_doctors/', manage_doctors, name='manage_doctors'),
    path('doctor/<int:doctor_id>/edit/', edit_doctor_ajax, name='edit_doctor_ajax'),
    path('doctor/<int:doctor_id>/delete/', delete_doctor_ajax, name='delete_doctor_ajax'),

    path('add_doctor/', add_doctor, name='add_doctor'),
   
    # Facility CRUD operations
    path('update-facility/', views.update_facility, name='update_facility'),
    path('delete-facility/<int:facility_id>/', views.delete_facility, name='delete_facility'),

    path('download-credentials/<int:facility_id>/', download_hospital_credentials, name='download_hospital_credentials'),

    # Credentials management
    path('request-credentials/', request_credentials_email, name='request_credentials_email'),
    path('api/request-credentials-sms/', request_credentials_sms, name='request_credentials_sms'),
    path('document-upload/', upload_documents, name='upload_documents'),
    path('upload-success/', success_page, name='success_page'),
    # SMS functionality
    path('send-sms/', views.send_verification_sms, name='send_verification_sms'),
    # User management
    path('admin_details/', views.admin_details, name='manage_users'),
    path('update_user/', views.update_user, name='update_user'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('get_user_password/<int:user_id>/', views.get_user_password, name='get_user_password'),
]