from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Course, Enrollment, Question, Choice, Submission


def registration_request(request):
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            pass
        if not user_exist:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            return render(request, 'onlinecourse/user_registration_bootstrap.html',
                          {'message': 'User already exists.'})


def login_request(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            return render(request, 'onlinecourse/user_login_bootstrap.html',
                          {'message': 'Invalid credentials.'})
    return render(request, 'onlinecourse/user_login_bootstrap.html')


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def index(request):
    courses = Course.objects.all()
    context = {'course_list': courses}
    return render(request, 'onlinecourse/course_list_bootstrap.html', context)


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if user.is_authenticated:
        try:
            Enrollment.objects.get(user=user, course=course)
        except:
            Enrollment.objects.create(user=user, course=course, mode='honor')
            course.total_enrollment += 1
            course.save()
    return HttpResponseRedirect(
        reverse('onlinecourse:course_details_bootstrap', args=(course.id,))
    )


def course_details(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    context = {'course': course}
    return render(request, 'onlinecourse/course_details_bootstrap.html', context)


def submit(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    chosen_ids = request.POST.getlist('choice')
    selected_choices = Choice.objects.filter(id__in=chosen_ids)
    submission.choices.set(selected_choices)
    submission.save()
    return HttpResponseRedirect(
        reverse('onlinecourse:show_exam_result', args=(course_id, submission.id))
    )


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    choices = submission.choices.all()
    total_score = 0
    for question in course.question_set.all():
        selected_ids = choices.filter(
            question=question
        ).values_list('id', flat=True)
        if question.is_get_score(selected_ids):
            total_score += question.grade
    context = {
        'course': course,
        'submission': submission,
        'choices': choices,
        'total_score': total_score,
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)