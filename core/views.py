from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from lms_core.models import Course, Subject


def index(request):
    return render(request, 'core/index.html')
