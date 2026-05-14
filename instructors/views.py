from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CourseForm, LessonForm, QuizForm, QuestionForm, ChoiceForm
from lms_core.models import Course, Lesson, Quiz, Question, Choice, QuizAttempt


@login_required
def instructor_dashboard(request):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')

    from django.db.models import Count, Sum

    courses = Course.objects.filter(instructor=request.user).select_related('subject')
    total_lessons = Lesson.objects.filter(course__in=courses).count()
    total_quizzes = Quiz.objects.filter(course__in=courses).count()

    # Class overview counts
    class_8_courses = courses.filter(target_class=8).count()
    class_9_courses = courses.filter(target_class=9).count()
    class_10_courses = courses.filter(target_class=10).count()

    # Student progress summary
    quiz_attempts = QuizAttempt.objects.filter(quiz__course__in=courses)
    total_quiz_attempts = quiz_attempts.count()
    total_students = quiz_attempts.values('student').distinct().count()
    total_views = Lesson.objects.filter(course__in=courses).aggregate(Sum('views'))['views__sum'] or 0

    # Recent student activity (last 5 quiz attempts)
    recent_activity = quiz_attempts.select_related(
        'student', 'quiz', 'quiz__course'
    ).order_by('-submitted_at')[:5]

    # Smart reminders
    reminders = []
    for course in courses:
        if course.quizzes.count() == 0:
            reminders.append({
                'icon': '📝',
                'text': f'Create a quiz for "{course.title}"',
                'type': 'warning'
            })
        if course.lessons.count() < 2:
            reminders.append({
                'icon': '🎥',
                'text': f'Add more lessons to "{course.title}"',
                'type': 'info'
            })
    if not reminders:
        reminders.append({
            'icon': '✅',
            'text': 'All courses are well-structured. Great job!',
            'type': 'success'
        })

    context = {
        'courses': courses,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'class_8_courses': class_8_courses,
        'class_9_courses': class_9_courses,
        'class_10_courses': class_10_courses,
        'total_students': total_students,
        'total_quiz_attempts': total_quiz_attempts,
        'total_views': total_views,
        'recent_activity': recent_activity,
        'reminders': reminders,
    }
    return render(request, 'instructors/instructor_dashboard.html', context)


@login_required
def course_create(request):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            # Create Course
            course = form.save(commit=False)
            course.title = form.cleaned_data['lesson_title']  # Use lesson title as course title for now
            course.instructor = request.user
            course.save()

            # Create first Lesson
            Lesson.objects.create(
                course=course,
                title=form.cleaned_data['lesson_title'],
                video_url=form.cleaned_data['video_url'],
                document=form.cleaned_data['document'],
                notes=form.cleaned_data['notes']
            )

            messages.success(request, "Lesson and Course added successfully!")
            return redirect('instructor_dashboard')
    else:
        form = CourseForm()
    return render(request, 'instructors/course_form.html', {'form': form, 'title': 'Add Lesson'})


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
    return render(request, 'instructors/course_detail.html', context)


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
    return render(request, 'instructors/lesson_form.html', {'form': form, 'course': course})


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
            messages.success(request, f"Quiz created! Please add your {quiz.number_of_questions} questions.")
            return redirect('quiz_bulk_questions', quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'instructors/quiz_form.html', {'form': form, 'course': course})


@login_required
def quiz_detail_instructor(request, pk):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')

    quiz = get_object_or_404(Quiz, pk=pk, course__instructor=request.user)
    questions = quiz.questions.all()

    return render(request, 'instructors/quiz_detail.html', {'quiz': quiz, 'questions': questions})


from django.forms import formset_factory
from .forms import BulkQuestionForm

@login_required
def quiz_bulk_questions(request, quiz_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')

    quiz = get_object_or_404(Quiz, pk=quiz_id, course__instructor=request.user)
    
    # Check if questions have already been added to prevent overriding or double-adding
    if quiz.questions.count() > 0:
        messages.info(request, "Features for bulk-editing existing questions are restricted to single-edit mode for safety.")
        return redirect('quiz_detail_instructor', pk=quiz.id)

    QuestionFormSet = formset_factory(
        BulkQuestionForm, 
        extra=quiz.number_of_questions, 
        max_num=quiz.number_of_questions,
        min_num=quiz.number_of_questions,
        validate_min=True, 
        validate_max=True
    )

    if request.method == 'POST':
        formset = QuestionFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    question = Question.objects.create(
                        quiz=quiz,
                        text=form.cleaned_data['text'],
                        marks=form.cleaned_data['marks'],
                        explanation=form.cleaned_data.get('explanation', '')
                    )
                    
                    correct_opt = form.cleaned_data['correct_option']
                    
                    Choice.objects.create(question=question, text=form.cleaned_data['option_a'], is_correct=(correct_opt == 'A'))
                    Choice.objects.create(question=question, text=form.cleaned_data['option_b'], is_correct=(correct_opt == 'B'))
                    Choice.objects.create(question=question, text=form.cleaned_data['option_c'], is_correct=(correct_opt == 'C'))
                    Choice.objects.create(question=question, text=form.cleaned_data['option_d'], is_correct=(correct_opt == 'D'))

            messages.success(request, f"Successfully added {quiz.number_of_questions} questions!")
            return redirect('quiz_detail_instructor', pk=quiz.id)
        else:
            messages.error(request, "Please correct the errors before saving.")
    else:
        formset = QuestionFormSet()

    return render(request, 'instructors/bulk_question_form.html', {'quiz': quiz, 'formset': formset})


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
    return render(request, 'instructors/question_form.html', context)


@login_required
def student_performance(request):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')

    # Base query
    attempts = QuizAttempt.objects.filter(
        quiz__course__instructor=request.user
    ).select_related('student', 'student__student_profile', 'quiz', 'quiz__course')

    # Filter context
    courses = Course.objects.filter(instructor=request.user)
    quizzes = Quiz.objects.filter(course__instructor=request.user)

    # Apply filters
    course_id = request.GET.get('course_id')
    class_id = request.GET.get('class_id')
    quiz_id = request.GET.get('quiz_id')
    student_name = request.GET.get('student_name')

    if course_id:
        attempts = attempts.filter(quiz__course_id=course_id)
    if class_id:
        attempts = attempts.filter(student__student_profile__current_class=class_id)
    if quiz_id:
        attempts = attempts.filter(quiz_id=quiz_id)
    if student_name:
        attempts = attempts.filter(student__first_name__icontains=student_name) | \
                   attempts.filter(student__last_name__icontains=student_name) | \
                   attempts.filter(student__username__icontains=student_name)

    attempts = attempts.order_by('-submitted_at')

    context = {
        'attempts': attempts,
        'courses': courses,
        'quizzes': quizzes,
        'filters': {
            'course_id': course_id,
            'class_id': class_id,
            'quiz_id': quiz_id,
            'student_name': student_name or '',
        }
    }
    return render(request, 'instructors/student_performance.html', context)


@login_required
def quiz_analytics(request, quiz_pk):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')

    quiz = get_object_or_404(Quiz, pk=quiz_pk, course__instructor=request.user)
    
    # We want to primarily analyze the *best* attempt of each student who took this quiz
    attempts = QuizAttempt.objects.filter(quiz=quiz, is_best=True)
    
    total_students = attempts.count()
    
    if total_students == 0:
        return render(request, 'instructors/quiz_analytics.html', {
            'quiz': quiz,
            'has_data': False
        })
        
    from django.db.models import Avg, Max, Min
    
    stats = attempts.aggregate(
        avg_score=Avg('percentage'),
        max_score=Max('percentage'),
        min_score=Min('percentage')
    )
    
    pass_mark = quiz.pass_percentage
    passed_count = attempts.filter(percentage__gte=pass_mark).count()
    failed_count = total_students - passed_count
    
    # Identify Top Performers (Top 5 scores)
    top_performers = attempts.order_by('-percentage')[:5]
    
    # Identify Needs Improvement (Bottom 5 scores)
    needs_improvement = attempts.order_by('percentage')[:5]
    
    context = {
        'quiz': quiz,
        'has_data': True,
        'total_students': total_students,
        'avg_score': round(stats['avg_score'] or 0, 1),
        'max_score': round(stats['max_score'] or 0, 1),
        'min_score': round(stats['min_score'] or 0, 1),
        'passed_count': passed_count,
        'failed_count': failed_count,
        'top_performers': top_performers,
        'needs_improvement': needs_improvement,
    }
    
    return render(request, 'instructors/quiz_analytics.html', context)


# ── edit & delete lessons/quizzes ─────────────────────────────────────────────

@login_required
def lesson_edit(request, lesson_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    lesson = get_object_or_404(Lesson, pk=lesson_id, course__instructor=request.user)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated successfully!")
            return redirect('course_detail_instructor', pk=lesson.course.id)
    else:
        form = LessonForm(instance=lesson)
        
    return render(request, 'instructors/lesson_form.html', {'form': form, 'course': lesson.course, 'is_edit': True})


@login_required
def lesson_delete(request, lesson_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    lesson = get_object_or_404(Lesson, pk=lesson_id, course__instructor=request.user)
    course_id = lesson.course.id
    
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, "Lesson deleted successfully.")
        return redirect('course_detail_instructor', pk=course_id)
        
    return render(request, 'instructors/confirm_delete.html', {
        'title': lesson.title,
        'type': 'Lesson',
        'cancel_url': f'/instructors/course/{course_id}/'
    })


@login_required
def quiz_edit(request, quiz_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    quiz = get_object_or_404(Quiz, pk=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, "Quiz updated successfully!")
            return redirect('course_detail_instructor', pk=quiz.course.id)
    else:
        form = QuizForm(instance=quiz)
        
    return render(request, 'instructors/quiz_form.html', {'form': form, 'course': quiz.course, 'is_edit': True})


@login_required
def quiz_delete(request, quiz_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    quiz = get_object_or_404(Quiz, pk=quiz_id, course__instructor=request.user)
    course_id = quiz.course.id
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Quiz deleted successfully.")
        return redirect('course_detail_instructor', pk=course_id)
        
    return render(request, 'instructors/confirm_delete.html', {
        'title': quiz.title,
        'type': 'Quiz',
        'cancel_url': f'/instructors/course/{course_id}/'
    })


@login_required
def question_edit(request, question_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    question = get_object_or_404(Question, pk=question_id, quiz__course__instructor=request.user)
    quiz = question.quiz
    choices = list(question.choices.all())
    
    c1_instance = choices[0] if len(choices) > 0 else None
    c2_instance = choices[1] if len(choices) > 1 else None
    c3_instance = choices[2] if len(choices) > 2 else None
    c4_instance = choices[3] if len(choices) > 3 else None

    if request.method == 'POST':
        q_form = QuestionForm(request.POST, instance=question)
        c1_form = ChoiceForm(request.POST, prefix='c1', instance=c1_instance)
        c2_form = ChoiceForm(request.POST, prefix='c2', instance=c2_instance)
        c3_form = ChoiceForm(request.POST, prefix='c3', instance=c3_instance)
        c4_form = ChoiceForm(request.POST, prefix='c4', instance=c4_instance)

        if q_form.is_valid() and c1_form.is_valid() and c2_form.is_valid() and c3_form.is_valid() and c4_form.is_valid():
            q_form.save()
            
            for c_form in [c1_form, c2_form, c3_form, c4_form]:
                if c_form.instance.pk:
                    c_form.save()
                else:
                    choice = c_form.save(commit=False)
                    choice.question = question
                    choice.save()

            messages.success(request, "Question updated successfully!")
            return redirect('quiz_detail_instructor', pk=quiz.id)
    else:
        q_form = QuestionForm(instance=question)
        c1_form = ChoiceForm(prefix='c1', instance=c1_instance)
        c2_form = ChoiceForm(prefix='c2', instance=c2_instance)
        c3_form = ChoiceForm(prefix='c3', instance=c3_instance)
        c4_form = ChoiceForm(prefix='c4', instance=c4_instance)

    context = {
        'quiz': quiz,
        'q_form': q_form,
        'c1_form': c1_form,
        'c2_form': c2_form,
        'c3_form': c3_form,
        'c4_form': c4_form,
        'is_edit': True,
    }
    return render(request, 'instructors/question_form.html', context)


@login_required
def question_delete(request, question_id):
    if request.user.role != 'INSTRUCTOR':
        return redirect('dashboard')
        
    question = get_object_or_404(Question, pk=question_id, quiz__course__instructor=request.user)
    quiz_id = question.quiz.id
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, "Question deleted successfully.")
        return redirect('quiz_detail_instructor', pk=quiz_id)
        
    return render(request, 'instructors/confirm_delete.html', {
        'title': question.text[:50] + ("..." if len(question.text) > 50 else ""),
        'type': 'Question',
        'cancel_url': f'/instructors/quiz/{quiz_id}/'
    })

