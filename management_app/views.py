from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.forms import AdminUserCreateForm
from lms_core.models import Course, Subject, Lesson, User, Quiz
import csv
from django.http import HttpResponse


@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    from django.db.models import Count, Avg, Max, Q
    from django.db.models.functions import TruncMonth
    from lms_core.models import Quiz, QuizAttempt, StudentProfile, User
    import json

    total_students = User.objects.filter(role='STUDENT').count()
    total_instructors = User.objects.filter(role='INSTRUCTOR').count()
    total_courses = Course.objects.count()
    total_lessons = Lesson.objects.count()
    total_quizzes = Quiz.objects.count()
    total_subjects = Subject.objects.count()

    popular_lessons = Lesson.objects.select_related('course', 'course__instructor').order_by('-views')[:5]

    # Recent students (last 5)
    recent_students = User.objects.filter(role='STUDENT').select_related('student_profile').order_by('-date_joined')[:5]

    # Recent courses (last 5)
    recent_courses = Course.objects.select_related('subject', 'instructor').order_by('-created_at')[:5]

    # --- Chart Data ---

    # Student growth by month (last 6 months)
    student_growth = (
        User.objects.filter(role='STUDENT')
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )[:6]
    growth_labels = [entry['month'].strftime('%b %Y') if entry['month'] else '' for entry in student_growth]
    growth_data = [entry['count'] for entry in student_growth]

    # Course distribution by subject
    subject_dist = Subject.objects.annotate(course_count=Count('courses')).filter(course_count__gt=0)
    dist_labels = [s.name for s in subject_dist]
    dist_data = [s.course_count for s in subject_dist]

    # Enrollment per course (top 6 by lesson count as proxy)
    top_courses = Course.objects.annotate(lesson_count=Count('lessons')).order_by('-lesson_count')[:6]
    enroll_labels = [c.title[:20] for c in top_courses]
    enroll_data = [c.lesson_count for c in top_courses]

    # --- New Advanced Analytics ---
    
    # 1 & 2. Average Score & Total Quiz Attempts
    total_quiz_attempts = QuizAttempt.objects.count()
    overall_avg_score = QuizAttempt.objects.aggregate(avg=Avg('percentage'))['avg']
    avg_score_display = round(overall_avg_score) if overall_avg_score is not None else 0

    # 3. Class-wise Performance
    classes = [8, 9, 10]
    perf_labels = [f"Class {c}" for c in classes]
    perf_data = []
    for c in classes:
        avg = QuizAttempt.objects.filter(student__student_profile__current_class=c).aggregate(avg=Avg('percentage'))['avg']
        perf_data.append(round(avg) if avg is not None else 0)

    # 4. Top Performers
    top_performers = User.objects.filter(role='STUDENT').annotate(
        avg_score=Avg('quiz_attempts__percentage'),
        best_score=Max('quiz_attempts__percentage'),
        total_attempts=Count('quiz_attempts')
    ).filter(total_attempts__gt=0).order_by('-avg_score')[:5]

    # 5. Quiz Analytics
    quiz_analytics = Quiz.objects.annotate(
        total_attempts=Count('attempts'),
        avg_score=Avg('attempts__percentage'),
        highest_score=Max('attempts__percentage')
    ).filter(total_attempts__gt=0).select_related('course', 'course__subject')

    most_attempted_quizzes = quiz_analytics.order_by('-total_attempts')[:5]
    hardest_quizzes = quiz_analytics.order_by('avg_score')[:5]
    best_performing_quizzes = quiz_analytics.order_by('-avg_score')[:5]

    context = {
        'total_students': total_students,
        'total_instructors': total_instructors,
        'total_courses': total_courses,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'total_subjects': total_subjects,
        'popular_lessons': popular_lessons,
        'recent_students': recent_students,
        'recent_courses': recent_courses,
        # Chart data as JSON
        'growth_labels': json.dumps(growth_labels),
        'growth_data': json.dumps(growth_data),
        'dist_labels': json.dumps(dist_labels),
        'dist_data': json.dumps(dist_data),
        'enroll_labels': json.dumps(enroll_labels),
        'enroll_data': json.dumps(enroll_data),
        
        # Advanced Analytics Additions
        'total_quiz_attempts': total_quiz_attempts,
        'avg_score_display': avg_score_display,
        'perf_labels': json.dumps(perf_labels),
        'perf_data': json.dumps(perf_data),
        'top_performers': top_performers,
        'most_attempted_quizzes': most_attempted_quizzes,
        'hardest_quizzes': hardest_quizzes,
        'best_performing_quizzes': best_performing_quizzes,
    }
    return render(request, 'management_app/admin_dashboard.html', context)


@login_required
def manage_students(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    students = User.objects.filter(role='STUDENT').prefetch_related('student_profile', 'quiz_attempts')
    subjects = Subject.objects.all().order_by('name')
    
    # Filtering
    subject_id = request.GET.get('subject')
    class_id = request.GET.get('class')

    if class_id:
        students = students.filter(student_profile__current_class=class_id)
    
    if subject_id:
        target_classes = Course.objects.filter(subject_id=subject_id).values_list('target_class', flat=True).distinct()
        students = students.filter(student_profile__current_class__in=target_classes)

    # Add enrolled courses to each student object for the view
    for student in students:
        current_class = getattr(student.student_profile, 'current_class', None)
        if current_class:
            student.enrolled_courses_list = Course.objects.filter(target_class=current_class)
        else:
            student.enrolled_courses_list = []

    context = {
        'users': students,
        'subjects': subjects,
        'title': 'Manage Students',
        'user_type': 'students',
        'selected_subject': subject_id,
        'selected_class': class_id,
    }
    return render(request, 'management_app/manage_students.html', context)


@login_required
def manage_instructors(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    instructors = User.objects.filter(role='INSTRUCTOR').prefetch_related('taught_courses')

    context = {
        'users': instructors,
        'title': 'Manage Instructors',
        'user_type': 'instructors'
    }
    return render(request, 'management_app/manage_instructors.html', context)


@login_required
def manage_subjects(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    subjects = Subject.objects.all().order_by('name')
    context = {
        'subjects': subjects,
        'title': 'Manage Subjects'
    }
    return render(request, 'management_app/manage_subjects.html', context)


@login_required
def manage_courses(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    courses = Course.objects.all().order_by('-created_at')
    context = {
        'courses': courses,
        'title': 'Manage Courses'
    }
    return render(request, 'management_app/manage_courses.html', context)


@login_required
def course_detail(request, pk):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    course = get_object_or_404(Course, pk=pk)
    lessons = course.lessons.all()
    quizzes = course.quizzes.all()

    context = {
        'course': course,
        'lessons': lessons,
        'quizzes': quizzes,
    }
    return render(request, 'management_app/course_detail.html', context)


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

    return render(request, 'management_app/subject_form.html', {'title': 'Create Subject'})


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

    return render(request, 'management_app/subject_form.html', {'subject': subject, 'title': 'Edit Subject'})


@login_required
def delete_subject(request, pk):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, "Subject deleted successfully!")
        return redirect('manage_subjects')

    return render(request, 'management_app/confirm_delete.html', {
        'object': subject,
        'type': 'subject',
        'cancel_url': 'manage_subjects'
    })


@login_required
def create_user(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Instructor {user.username} created successfully!")
            return redirect('manage_instructors')
    else:
        form = AdminUserCreateForm()

    return render(request, 'management_app/user_form.html', {'form': form, 'title': 'Create New Instructor'})


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

    return render(request, 'management_app/user_form.html', {
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

    return render(request, 'management_app/confirm_delete.html', {
        'object': target_user,
        'type': 'user',
        'cancel_url': 'manage_students' if target_user.role == 'STUDENT' else 'manage_instructors'
    })


@login_required
def manage_quizzes(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    quizzes = Quiz.objects.select_related('course', 'course__subject').order_by('course__subject__name', 'title')
    
    context = {
        'quizzes': quizzes,
        'title': 'All Quizzes'
    }
    return render(request, 'management_app/list_quizzes.html', context)


@login_required
def manage_lessons(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    lessons = Lesson.objects.select_related('course', 'course__subject').order_by('course__subject__name', 'title')
    
    context = {
        'lessons': lessons,
        'title': 'All Lessons'
    }
    return render(request, 'management_app/list_lessons.html', context)


@login_required
def export_student_report(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    students = User.objects.filter(role='STUDENT').prefetch_related('student_profile')
    
    # Apply same filters as manage_students
    subject_id = request.GET.get('subject')
    class_id = request.GET.get('class')

    if class_id:
        students = students.filter(student_profile__current_class=class_id)
    if subject_id:
        target_classes = Course.objects.filter(subject_id=subject_id).values_list('target_class', flat=True).distinct()
        students = students.filter(student_profile__current_class__in=target_classes)

    # Create CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Username', 'Full Name', 'Email', 'Current Class', 'Enrolled Courses', 'Status', 'Joined Date'])
    
    for student in students:
        # Get courses for this student's class
        current_class = getattr(student.student_profile, 'current_class', None)
        if current_class:
            student_courses = Course.objects.filter(target_class=current_class)
            course_titles = ", ".join([c.title for c in student_courses])
        else:
            course_titles = "N/A"
            
        writer.writerow([
            student.username,
            student.get_full_name() or student.username,
            student.email or "-",
            f"Class {current_class}" if current_class else "N/A",
            course_titles,
            "Active" if student.is_active else "Inactive",
            student.date_joined.strftime('%Y-%m-%d %H:%M') if student.date_joined else "N/A"
        ])
        
    return response


@login_required
def student_report_view(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    students = User.objects.filter(role='STUDENT').select_related('student_profile')
    
    # Apply same filters
    subject_id = request.GET.get('subject')
    class_id = request.GET.get('class')

    if class_id:
        students = students.filter(student_profile__current_class=class_id)
    if subject_id:
        target_classes = Course.objects.filter(subject_id=subject_id).values_list('target_class', flat=True).distinct()
        students = students.filter(student_profile__current_class__in=target_classes)

    # Prepare data
    report_data = []
    for student in students:
        current_class = getattr(student.student_profile, 'current_class', None)
        if current_class:
            student_courses = Course.objects.filter(target_class=current_class)
            course_titles = ", ".join([c.title for c in student_courses])
        else:
            course_titles = "N/A"
            
        report_data.append({
            'username': student.username,
            'full_name': student.get_full_name() or student.username,
            'email': student.email,
            'class': f"Class {current_class}" if current_class else "N/A",
            'courses': course_titles
        })

    context = {
        'report_data': report_data,
        'title': 'Student Enrollment Report',
        'selected_subject': Subject.objects.get(id=subject_id).name if subject_id else "All Subjects",
        'selected_class': f"Class {class_id}" if class_id else "All Classes"
    }
    return render(request, 'management_app/student_report.html', context)
