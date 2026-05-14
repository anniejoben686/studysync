from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('INSTRUCTOR', 'Instructor'),
        ('STUDENT', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')

class StudentProfile(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    current_class = models.IntegerField(choices=[(8, 'Class 8'), (9, 'Class 9'), (10, 'Class 10')], default=8)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    phone_number = models.CharField(max_length=10, default='')
    promoted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Class {self.current_class}"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses', limit_choices_to={'role': 'INSTRUCTOR'})
    target_class = models.IntegerField(choices=[(8, 'Class 8'), (9, 'Class 9'), (10, 'Class 10')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (Class {self.target_class})"

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or external video URL")
    document = models.FileField(upload_to='lessons/documents/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or document text")
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Quiz(models.Model):
    ATTEMPT_POLICY_CHOICES = [
        ('HIGHEST', 'Highest Score'),
        ('LATEST', 'Latest Score'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    
    # New Configuration Fields
    number_of_questions = models.PositiveIntegerField(default=1, help_text="Number of questions in this quiz")
    duration = models.IntegerField(default=0, help_text="Duration in minutes. 0 for unlimited.")
    max_attempts = models.IntegerField(default=0, help_text="0 for unlimited attempts.")
    pass_percentage = models.IntegerField(default=40)
    attempt_policy = models.CharField(max_length=20, choices=ATTEMPT_POLICY_CHOICES, default='HIGHEST')
    
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    
    shuffle_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=False)
    show_score = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    marks = models.IntegerField(default=1)
    explanation = models.TextField(blank=True, null=True, help_text="Feedback shown after submission.")

    def __str__(self):
        return self.text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class QuizAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', limit_choices_to={'role': 'STUDENT'})
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    marks_obtained = models.IntegerField(default=0)
    total_marks = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    attempt_number = models.IntegerField(default=1)
    is_best = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Keep backward-compatible alias so old templates using attempt.score still work
    @property
    def score(self):
        return round(self.percentage)

    # Keep backward-compatible alias
    @property
    def attempted_on(self):
        return self.submitted_at

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - Attempt {self.attempt_number} ({self.percentage:.1f}%)"
