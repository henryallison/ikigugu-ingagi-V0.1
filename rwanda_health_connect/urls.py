from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('home/', include('core.urls')),
    path('referrals/', include('referral.urls')),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),  # Add this line
    path('manage_hospital/', include('manage_hospital.urls')),
    path('patients/', include('patients.urls')),
    path('find-hospital/', include('find_hospital.urls'), name='find_hospital'),
]