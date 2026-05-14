from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import StudentAdminLoginForm, InstructorLoginForm

urlpatterns = [
    path('register/', views.register, name='register'),
    path('student-register/', views.register, name='student_register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=StudentAdminLoginForm
    ), name='login'),
    path('instructor-login/', auth_views.LoginView.as_view(
        template_name='accounts/instructor_login.html',
        authentication_form=InstructorLoginForm
    ), name='instructor_login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change_form.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
]
