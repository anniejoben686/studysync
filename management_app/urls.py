from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('students/', views.manage_students, name='manage_students'),
    path('instructors/', views.manage_instructors, name='manage_instructors'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:pk>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:pk>/delete/', views.delete_user, name='delete_user'),
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('subjects/create/', views.create_subject, name='create_subject'),
    path('subjects/<int:pk>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<int:pk>/delete/', views.delete_subject, name='delete_subject'),
    path('courses/', views.manage_courses, name='manage_courses'),
    path('courses/<int:pk>/', views.course_detail, name='admin_course_detail'),
    path('quizzes/', views.manage_quizzes, name='manage_quizzes'),
    path('lessons/', views.manage_lessons, name='manage_lessons'),
    path('export-students/', views.export_student_report, name='export_student_report'),
    path('view-report/', views.student_report_view, name='student_report_view'),
]
