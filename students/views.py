from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Count
from lms_core.models import Course, Subject, Quiz, QuizAttempt, Lesson, Choice


# ── helpers ──────────────────────────────────────────────────────────────────

def _performance_label(pct):
    if pct >= 85:
        return ('Outstanding', 'success')
    elif pct >= 60:
        return ('Good', 'good')
    elif pct >= 40:
        return ('Average', 'average')
    else:
        return ('Needs Work', 'danger')


# ── student dashboard ─────────────────────────────────────────────────────────

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
    return render(request, 'students/student_dashboard.html', context)


# ── courses ───────────────────────────────────────────────────────────────────

@login_required
def student_courses(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    student_class = request.user.student_profile.current_class
    courses = Course.objects.filter(target_class=student_class)
    return render(request, 'students/courses.html', {'courses': courses})


# ── quizzes list ──────────────────────────────────────────────────────────────

@login_required
def student_quizzes(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    student_class = request.user.student_profile.current_class
    quizzes = Quiz.objects.filter(course__target_class=student_class)

    # Annotate each quiz with this student's attempt count and best %
    quiz_data = []
    for quiz in quizzes:
        student_attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz)
        attempt_count = student_attempts.count()
        best_attempt = student_attempts.filter(is_best=True).first()
        quiz_data.append({
            'quiz': quiz,
            'attempt_count': attempt_count,
            'best_pct': round(best_attempt.percentage) if best_attempt else None,
        })

    return render(request, 'students/quizzes.html', {'quiz_data': quiz_data})


# ── progress ──────────────────────────────────────────────────────────────────

@login_required
def student_progress(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    attempts = QuizAttempt.objects.filter(student=request.user).select_related('quiz', 'quiz__course')

    total_attempted = attempts.count()
    avg_pct = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
    best_attempt = attempts.filter(is_best=True).order_by('-percentage').first()
    latest_attempt = attempts.order_by('-submitted_at').first()

    # Annotate attempts with performance label
    annotated = []
    for a in attempts.order_by('-submitted_at'):
        label, css = _performance_label(a.percentage)
        annotated.append({
            'attempt': a,
            'label': label,
            'css': css,
        })

    context = {
        'annotated': annotated,
        'total_attempted': total_attempted,
        'avg_pct': round(avg_pct, 1),
        'best_attempt': best_attempt,
        'latest_attempt': latest_attempt,
    }
    return render(request, 'students/progress.html', context)


# ── course detail ─────────────────────────────────────────────────────────────

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
    return render(request, 'students/course_detail.html', context)


# ── lesson detail ─────────────────────────────────────────────────────────────

@login_required
def lesson_detail(request, pk):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    student_class = request.user.student_profile.current_class
    lesson = get_object_or_404(Lesson, pk=pk, course__target_class=student_class)

    lesson.views += 1
    lesson.save(update_fields=['views'])

    embed_url = None
    if lesson.video_url:
        import re
        url = lesson.video_url.strip()
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        ]
        video_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                break
        if video_id:
            embed_url = f'https://www.youtube.com/embed/{video_id}'

    context = {
        'lesson': lesson,
        'course': lesson.course,
        'embed_url': embed_url,
    }
    return render(request, 'students/lesson_detail.html', context)


# ── take quiz ─────────────────────────────────────────────────────────────────

@login_required
def take_quiz(request, quiz_pk):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    student_class = request.user.student_profile.current_class
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course__target_class=student_class)
    questions = quiz.questions.prefetch_related('choices').all()

    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'students/take_quiz.html', context)


# ── submit quiz ───────────────────────────────────────────────────────────────

@login_required
def submit_quiz(request, quiz_pk):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('take_quiz', quiz_pk=quiz_pk)

    student_class = request.user.student_profile.current_class
    quiz = get_object_or_404(Quiz, pk=quiz_pk, course__target_class=student_class)
    questions = quiz.questions.prefetch_related('choices').all()

    # ── Score calculation ─────────────────────────────────────────────────────
    marks_obtained = 0
    total_marks = questions.count()

    for question in questions:
        selected_id = request.POST.get(f'question_{question.id}')
        if selected_id:
            try:
                choice = question.choices.get(id=selected_id)
                if choice.is_correct:
                    marks_obtained += 1
            except Choice.DoesNotExist:
                pass

    percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0

    # ── Previous attempts for this student + quiz ─────────────────────────────
    prev_attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('attempt_number')
    attempt_number = prev_attempts.count() + 1
    prev_best_pct = prev_attempts.filter(is_best=True).values_list('percentage', flat=True).first() or 0
    prev_last_attempt = prev_attempts.order_by('-submitted_at').first()

    # ── Save new attempt ──────────────────────────────────────────────────────
    new_attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        marks_obtained=marks_obtained,
        total_marks=total_marks,
        percentage=round(percentage, 2),
        attempt_number=attempt_number,
        is_best=False,
    )

    # ── Update is_best flags ──────────────────────────────────────────────────
    if percentage >= prev_best_pct:
        prev_attempts.filter(is_best=True).update(is_best=False)
        new_attempt.is_best = True
        new_attempt.save(update_fields=['is_best'])

    # ── Class analytics (same quiz, same class) ───────────────────────────────
    class_attempts = QuizAttempt.objects.filter(
        quiz=quiz,
        student__student_profile__current_class=student_class,
    )
    class_avg = class_attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
    class_top = class_attempts.aggregate(Max('percentage'))['percentage__max'] or 0

    # Rank: count students who have a best attempt better than this score
    students_above = (
        QuizAttempt.objects
        .filter(quiz=quiz, student__student_profile__current_class=student_class, is_best=True)
        .values('student')
        .distinct()
        .filter(quiz=quiz)
    )
    # Simple rank: how many distinct students scored higher in their best attempt?
    better_count = QuizAttempt.objects.filter(
        quiz=quiz,
        student__student_profile__current_class=student_class,
        is_best=True,
        percentage__gt=percentage,
    ).values('student').distinct().count()
    student_rank = better_count + 1
    total_students = QuizAttempt.objects.filter(
        quiz=quiz,
        student__student_profile__current_class=student_class,
        is_best=True,
    ).values('student').distinct().count()

    # ── Class performance message ─────────────────────────────────────────────
    if student_rank == 1 and total_students >= 1:
        class_msg = f"Outstanding! You are the top scorer in your class for this quiz."
        class_msg_type = 'outstanding'
    elif percentage > class_avg:
        class_msg = f"Good work! You scored above the class average of {class_avg:.1f}%."
        class_msg_type = 'good'
    elif abs(percentage - class_avg) <= 5:
        class_msg = f"Nice attempt! Your score is close to the class average of {class_avg:.1f}%."
        class_msg_type = 'average'
    else:
        class_msg = f"Keep practicing. Your score is below the class average of {class_avg:.1f}%."
        class_msg_type = 'below'

    # ── Reattempt improvement message ─────────────────────────────────────────
    reattempt_msg = None
    reattempt_type = None
    if attempt_number > 1 and prev_last_attempt:
        delta = percentage - prev_last_attempt.percentage
        if delta > 0:
            reattempt_msg = f"Great improvement! You scored {delta:.1f}% higher than your previous attempt ({prev_last_attempt.percentage:.1f}%)."
            reattempt_type = 'improved'
        elif delta < 0:
            reattempt_msg = f"Your score dropped by {abs(delta):.1f}% from your previous attempt ({prev_last_attempt.percentage:.1f}%). Review the material and try again."
            reattempt_type = 'dropped'
        else:
            reattempt_msg = f"Same score as your previous attempt. Keep reviewing to push higher!"
            reattempt_type = 'same'

    # ── Store result context in session for quiz_result view ──────────────────
    request.session['quiz_result'] = {
        'quiz_title': quiz.title,
        'quiz_pk': quiz.pk,
        'marks_obtained': marks_obtained,
        'total_marks': total_marks,
        'percentage': round(percentage, 1),
        'attempt_number': attempt_number,
        'class_avg': round(class_avg, 1),
        'class_top': round(class_top, 1),
        'student_rank': student_rank,
        'total_students': total_students,
        'class_name': student_class,
        'class_msg': class_msg,
        'class_msg_type': class_msg_type,
        'reattempt_msg': reattempt_msg,
        'reattempt_type': reattempt_type,
        'is_best': new_attempt.is_best,
    }

    return redirect('quiz_result', quiz_pk=quiz_pk)


# ── quiz result ───────────────────────────────────────────────────────────────

@login_required
def quiz_result(request, quiz_pk):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')

    result = request.session.pop('quiz_result', None)
    if not result:
        return redirect('student_quizzes')

    label, css = _performance_label(result['percentage'])
    result['perf_label'] = label
    result['perf_css'] = css

    return render(request, 'students/quiz_result.html', {'result': result})
