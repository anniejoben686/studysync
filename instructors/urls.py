from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('course/new/', views.course_create, name='course_create'),
    path('course/<int:pk>/', views.course_detail_instructor, name='course_detail_instructor'),
    path('course/<int:course_id>/lesson/new/', views.lesson_create, name='lesson_create'),
    path('lesson/<int:lesson_id>/edit/', views.lesson_edit, name='lesson_edit'),
    path('lesson/<int:lesson_id>/delete/', views.lesson_delete, name='lesson_delete'),
    
    path('course/<int:course_id>/quiz/new/', views.quiz_create, name='quiz_create'),
    path('quiz/<int:quiz_id>/bulk-questions/', views.quiz_bulk_questions, name='quiz_bulk_questions'),
    path('quiz/<int:pk>/', views.quiz_detail_instructor, name='quiz_detail_instructor'),
    path('quiz/<int:quiz_id>/edit/', views.quiz_edit, name='quiz_edit'),
    path('quiz/<int:quiz_id>/delete/', views.quiz_delete, name='quiz_delete'),
    
    path('quiz/<int:quiz_id>/question/new/', views.question_create, name='question_create'),
    path('question/<int:question_id>/edit/', views.question_edit, name='question_edit'),
    path('question/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    
    path('quiz/<int:quiz_pk>/analytics/', views.quiz_analytics, name='quiz_analytics'),
    path('performance/', views.student_performance, name='student_performance'),
]
