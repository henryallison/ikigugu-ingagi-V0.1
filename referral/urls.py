# referral/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_referral, name='manage_referral'),
    path('track/', views.track_referral, name='track_referral'),
    path('details/', views.referral_details, name='referral_details'),
    path('list/', views.referral_list, name='referral_list'),
    path('add/', views.add_referral, name='add_referral'),
    path('patients/', views.patients_referrals, name='patients_referral'),

    # ADD THESE TWO LINES FOR YOUR AJAX VIEWS
    path('ajax/get_hospital_and_doctors/', views.get_hospital_and_doctors_for_patient, name='get_hospital_and_doctors_for_patient'),
    path('ajax/get_doctors_for_hospital/', views.get_doctors_for_hospital, name='get_doctors_for_hospital'),
    path('<int:pk>/update/', views.referral_update_view, name='referral_update'),  # <--- CHANGED
    path('<int:pk>/delete/', views.referral_delete_view, name='referral_delete'),  # <--- CHANGED

]