from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import StudentRegistrationForm


def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('student_dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif user.role == 'INSTRUCTOR':
        return redirect('instructor_dashboard')
    else:
        return redirect('student_dashboard')
