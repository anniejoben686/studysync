from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, Course, Lesson, Quiz, Question, Choice

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'subject', 'target_class']

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video_url', 'document']

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    current_class = forms.ChoiceField(
        choices=[(8, 'Class 8'), (9, 'Class 9'), (10, 'Class 10')],
        required=True,
        help_text="Select your current class"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'current_class')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'STUDENT'
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                current_class=self.cleaned_data.get('current_class')
            )
        return user
