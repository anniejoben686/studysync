from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, Subject, Course, Lesson, Quiz, Question, Choice, QuizAttempt

class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']

admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile)
admin.site.register(Subject)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'instructor', 'target_class', 'created_at')
    list_filter = ('target_class', 'subject')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'views', 'created_at')
    list_filter = ('course',)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_at')
    inlines = [QuestionInline]

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz')
    inlines = [ChoiceInline]

admin.site.register(Choice)
admin.site.register(QuizAttempt)
