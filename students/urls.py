from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('courses/', views.student_courses, name='student_courses'),
    path('quizzes/', views.student_quizzes, name='student_quizzes'),
    path('progress/', views.student_progress, name='student_progress'),
    path('course/<int:pk>/', views.course_detail_student, name='course_detail_student'),
    path('lesson/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('quiz/<int:quiz_pk>/take/', views.take_quiz, name='take_quiz'),
    path('quiz/<int:quiz_pk>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/<int:quiz_pk>/result/', views.quiz_result, name='quiz_result'),
]

