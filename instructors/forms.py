from django import forms
from lms_core.models import Course, Lesson, Quiz, Question, Choice


class CourseForm(forms.ModelForm):
    lesson_title = forms.CharField(max_length=200, label="Lesson Title", required=True)
    video_url = forms.URLField(label="Upload Video URL", required=False, help_text="YouTube or external video URL")
    document = forms.FileField(label="Document", required=False)
    notes = forms.CharField(widget=forms.Textarea, label="Document Notes", required=False)

    class Meta:
        model = Course
        fields = ['subject', 'target_class']

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video_url', 'document', 'notes']
        labels = {
            'title': 'Lesson Title',
            'video_url': 'Upload Video URL',
            'notes': 'Document Notes',
        }


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'title', 'number_of_questions', 'duration', 'max_attempts', 'pass_percentage',  
            'attempt_policy', 'start_date', 'end_date', 'shuffle_questions', 
            'show_correct_answers', 'show_score', 'is_published'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'marks', 'explanation']
        widgets = {
            'explanation': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional feedback shown to students after submission'})
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']


class BulkQuestionForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter the question text'}),
        label='Question',
        required=True
    )
    marks = forms.IntegerField(initial=1, min_value=1, required=True, label='Marks')
    
    option_a = forms.CharField(max_length=200, required=True, label='Option A')
    option_b = forms.CharField(max_length=200, required=True, label='Option B')
    option_c = forms.CharField(max_length=200, required=True, label='Option C')
    option_d = forms.CharField(max_length=200, required=True, label='Option D')
    
    correct_option = forms.ChoiceField(
        choices=[('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ('D', 'Option D')],
        required=True,
        label='Correct Option'
    )
    
    explanation = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional feedback shown to students after submission'}),
        required=False,
        label='Explanation/Feedback'
    )
