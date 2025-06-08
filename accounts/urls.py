from django.urls import path
from .import views
from .views import login_view, logout_view, register_view, terms_of_service, privacy_policy, document_upload_view, about_us_view, contact_view

app_name = 'accounts'

urlpatterns = [
path('about-us/', about_us_view, name='about_us'),
    path('contact/', contact_view, name='contact'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('terms-of-service/', terms_of_service, name='terms_of_service'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('request-credentials/', views.request_credentials_view, name='request_credentials'), 
    path('document-upload/', views.document_upload_view, name='document_upload'),# 
    path('document-upload/', document_upload_view, name='document_upload'),

] 