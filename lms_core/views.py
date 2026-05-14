from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CourseForm, LessonForm, QuizForm, QuestionForm, ChoiceForm
from .models import Course, Subject, Lesson, Quiz, Question, Choice, QuizAttempt, User
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'lms_core/index.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif user.role == 'INSTRUCTOR':
        return redirect('instructor_dashboard')
    else:
        return redirect('student_dashboard')

@login_required
def student_dashboard(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    
    student_class = request.user.student_profile.current_class
    courses = Course.objects.filter(target_class=student_class)
    subjects = Subject.objects.filter(courses__in=courses).distinct()
    
    context = {
        'student_class': student_class,
        'courses': courses,
        'subjects': subjects,
    }
    return render(request, 'lms_core/student_dashboard.html', context)

@login_required
def student_courses(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    
    student_class = request.user.student_profile.current_class
    courses = Course.objects.filter(target_class=student_class)
    return render(request, 'lms_core/student/courses.html', {'courses': courses})

@login_required
def student_quizzes(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    
    student_class = request.user.student_profile.current_class
    quizzes = Quiz.objects.filter(course__target_class=student_class)
    return render(request, 'lms_core/student/quizzes.html', {'quizzes': quizzes})

@login_required
def student_progress(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    
    attempts = QuizAttempt.objects.filter(student=request.user).order_by('-attempted_on')
    return render(request, 'lms_core/student/progress.html', {'attempts': attempts})

@login_required
def course_detail_student(request, pk):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
    
    student_class = request.user.student_profile.current_class
    course = get_object_or_404(Course, pk=pk, target_class=student_class)
    lessons = course.lessons.all()
    quizzes = course.quizzes.all()
    
    context = {
        'course': course,
        'lessons': lessons,
        'quizzes': quizzes,
    }
    return render(request, 'lms_core/student/course_detail.html', context)

@login_required
def instructor_dashboard(request):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
    
    courses = Course.objects.filter(instructor=request.user)
    total_lessons = Lesson.objects.filter(course__in=courses).count()
    context = {
        'courses': courses,
        'total_lessons': total_lessons,
    }
    return render(request, 'lms_core/instructor_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    # Needs basic analytics like most watched videos and course count
    from django.db.models import Sum, Count
    from .models import Lesson, User
    
    total_students = User.objects.filter(role='STUDENT').count()
    total_instructors = User.objects.filter(role='INSTRUCTOR').count()
    total_courses = Course.objects.count()
    
    popular_lessons = Lesson.objects.order_by('-views')[:5]
    
    context = {
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'popular_lessons': popular_lessons,
    }
    return render(request, 'lms_core/admin_dashboard.html', context)

# --- Instructor Custom Views ---

@login_required
def course_create(request):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, "Course created successfully!")
            return redirect('instructor_dashboard')
    else:
        form = CourseForm()
    return render(request, 'lms_core/instructor/course_form.html', {'form': form, 'title': 'Create Course'})

@login_required
def course_detail_instructor(request, pk):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    lessons = course.lessons.all()
    quizzes = course.quizzes.all()
    
    context = {
        'course': course,
        'lessons': lessons,
        'quizzes': quizzes,
    }
    return render(request, 'lms_core/instructor/course_detail.html', context)

@login_required
def lesson_create(request, course_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, pk=course_id, instructor=request.user)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, "Lesson added successfully!")
            return redirect('course_detail_instructor', pk=course.id)
    else:
        form = LessonForm()
    return render(request, 'lms_core/instructor/lesson_form.html', {'form': form, 'course': course})

@login_required
def quiz_create(request, course_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, pk=course_id, instructor=request.user)
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.save()
            messages.success(request, "Quiz created! Now add some questions.")
            return redirect('quiz_detail_instructor', pk=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'lms_core/instructor/quiz_form.html', {'form': form, 'course': course})

@login_required
def quiz_detail_instructor(request, pk):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
    
    quiz = get_object_or_404(Quiz, pk=pk, course__instructor=request.user)
    questions = quiz.questions.all()
    
    return render(request, 'lms_core/instructor/quiz_detail.html', {'quiz': quiz, 'questions': questions})

@login_required
def question_create(request, quiz_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    quiz = get_object_or_404(Quiz, pk=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        q_form = QuestionForm(request.POST)
        c1_form = ChoiceForm(request.POST, prefix='c1')
        c2_form = ChoiceForm(request.POST, prefix='c2')
        c3_form = ChoiceForm(request.POST, prefix='c3')
        c4_form = ChoiceForm(request.POST, prefix='c4')
        
        if q_form.is_valid() and c1_form.is_valid() and c2_form.is_valid() and c3_form.is_valid() and c4_form.is_valid():
            question = q_form.save(commit=False)
            question.quiz = quiz
            question.save()
            
            for c_form in [c1_form, c2_form, c3_form, c4_form]:
                choice = c_form.save(commit=False)
                choice.question = question
                choice.save()
                
            messages.success(request, "Question added successfully!")
            return redirect('quiz_detail_instructor', pk=quiz.id)
    else:
        q_form = QuestionForm()
        c1_form = ChoiceForm(prefix='c1')
        c2_form = ChoiceForm(prefix='c2')
        c3_form = ChoiceForm(prefix='c3')
        c4_form = ChoiceForm(prefix='c4')
        
    context = {
        'quiz': quiz,
        'q_form': q_form,
        'c1_form': c1_form,
        'c2_form': c2_form,
        'c3_form': c3_form,
        'c4_form': c4_form,
    }
    return render(request, 'lms_core/instructor/question_form.html', context)

@login_required
def student_performance(request):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    # Get all quiz attempts for quizzes in courses taught by this instructor
    attempts = QuizAttempt.objects.filter(
        quiz__course__instructor=request.user
    ).order_by('-attempted_on')
    
    return render(request, 'lms_core/instructor/student_performance.html', {'attempts': attempts})

# --- Admin Management Views ---

@login_required
def manage_students(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    # Show students who have enrolled (have student profiles) and are attending (have quiz attempts)
    students = User.objects.filter(role='STUDENT').prefetch_related('student_profile', 'quiz_attempts')
    
    context = {
        'users': students,
        'title': 'Manage Students',
        'user_type': 'students'
    }
    return render(request, 'lms_core/admin/manage_students.html', context)

@login_required
def manage_instructors(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    # Show instructors who have been assigned courses
    instructors = User.objects.filter(role='INSTRUCTOR').prefetch_related('taught_courses')
    
    context = {
        'users': instructors,
        'title': 'Manage Instructors',
        'user_type': 'instructors'
    }
    return render(request, 'lms_core/admin/manage_instructors.html', context)

@login_required
def manage_subjects(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    subjects = Subject.objects.all().order_by('name')
    context = {
        'subjects': subjects,
        'title': 'Manage Subjects'
    }
    return render(request, 'lms_core/admin/manage_subjects.html', context)

@login_required
def manage_courses(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    courses = Course.objects.all().order_by('-created_at')
    context = {
        'courses': courses,
        'title': 'Manage Courses'
    }
    return render(request, 'lms_core/admin/manage_courses.html', context)

@login_required
def create_subject(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            Subject.objects.create(name=name, description=description)
            messages.success(request, "Subject created successfully!")
            return redirect('manage_subjects')
    
    return render(request, 'lms_core/admin/subject_form.html', {'title': 'Create Subject'})

@login_required
def edit_subject(request, pk):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        subject.name = request.POST.get('name')
        subject.description = request.POST.get('description')
        subject.save()
        messages.success(request, "Subject updated successfully!")
        return redirect('manage_subjects')
    
    return render(request, 'lms_core/admin/subject_form.html', {'subject': subject, 'title': 'Edit Subject'})

@login_required
def delete_subject(request, pk):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, "Subject deleted successfully!")
        return redirect('manage_subjects')
    
    return render(request, 'lms_core/admin/confirm_delete.html', {
        'object': subject,
        'type': 'subject',
        'cancel_url': 'manage_subjects'
    })

@login_required
def create_user(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.username} created successfully!")
            
            # Redirect to appropriate page based on user role
            if user.role == 'STUDENT':
                return redirect('manage_students')
            else:
                return redirect('manage_instructors')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'lms_core/admin/user_form.html', {'form': form, 'title': 'Create New Instructor'})

@login_required
def edit_user(request, pk):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    target_user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        target_user.username = request.POST.get('username')
        target_user.email = request.POST.get('email')
        target_user.first_name = request.POST.get('first_name')
        target_user.last_name = request.POST.get('last_name')
        target_user.role = request.POST.get('role')
        target_user.is_active = 'is_active' in request.POST
        target_user.save()
        messages.success(request, f"User {target_user.username} updated successfully!")
        
        # Redirect to appropriate page based on user role
        if target_user.role == 'STUDENT':
            return redirect('manage_students')
        else:
            return redirect('manage_instructors')
    
    return render(request, 'lms_core/admin/user_form.html', {
        'target_user': target_user, 
        'title': 'Edit User',
        'cancel_url': 'manage_students' if target_user.role == 'STUDENT' else 'manage_instructors'
    })

@login_required
def delete_user(request, pk):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    target_user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        role = target_user.role  # Store role before deletion
        target_user.delete()
        messages.success(request, "User deleted successfully!")
        
        # Redirect to appropriate page based on user role
        if role == 'STUDENT':
            return redirect('manage_students')
        else:
            return redirect('manage_instructors')
    
    return render(request, 'lms_core/admin/confirm_delete.html', {
        'object': target_user,
        'type': 'user',
        'cancel_url': 'manage_students' if target_user.role == 'STUDENT' else 'manage_instructors'
    })
