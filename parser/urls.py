from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('results/',views.results, name='results'),
    path("download/<str:file_type>/", views.download_results_file, name="download_results"),
    path('clear-session/', views.clear_session_and_home, name='clear_session_and_home'),
    path("api/screen_resumes/", views.api_screen_resumes, name="api_screen_resumes"),
]