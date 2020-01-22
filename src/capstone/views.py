from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from datetime import datetime
from . import models
from .watson import discovery as Dy
from .user import related_links
import pprint
import os, json


def index(request):
    return render(request, os.getcwd() + "/capstone/templates/index.html")

def logout(request):
    auth_logout(request)
    return redirect('/')

def login(request):
    if request.method == 'GET':
        return render(request, os.getcwd() + '/capstone/templates/registration/login.html')
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/')
        else:
            context = {'user_login_failed': True}
            return render(request, os.getcwd() + '/capstone/templates/registration/login.html', context=context)


def sign_up(request):
    if request.method == 'GET':
        return render(request, os.getcwd() + '/capstone/templates/registration/sign_up.html')
    elif request.method == 'POST':
        if User.objects.filter(username=request.POST.get('username')).exists():
            context = {'username_taken': True}
            return render(request, os.getcwd() + '/capstone/templates/registration/sign_up.html', context=context)
        elif ' ' in request.POST.get('username'):
            context = {'username_contains_spaces': True}
            return render(request, os.getcwd() + '/capstone/templates/registration/sign_up.html', context=context)
        elif len(request.POST.get('pwd1')) < 4:
            context = {'pwd_length': True}
            return render(request, os.getcwd() + '/capstone/templates/registration/sign_up.html', context=context)
        elif (request.POST.get('pwd1') != request.POST.get('pwd2')):
            context = {'pwd_mismatch': True}
            return render(request, os.getcwd() + '/capstone/templates/registration/sign_up.html', context=context)
        else:
            big_user = User.objects.create_user(username=request.POST.get('username'), password=request.POST.get('pwd1'))
            
            user = models.User()
            user.user = big_user
            user.history = json.dumps([])
            user.save()

            context = {'successful': True}
            return render(request, os.getcwd() + '/capstone/templates/registration/sign_up.html', context)

def get_results(request):
    query = request.POST.get("query")
    if not query:
        return HttpResponse("<h1> No results found </h1>")    

    passages = Dy.discover(query, True, True)
    context = {"passages": passages, "query": query}

    #    pp = pprint.PrettyPrinter(indent=4)
    #    pp.pprint(context)

    if request.user.is_authenticated:
        user = User.objects.get(username=request.user.username)
        my_user = models.User.objects.get(user=user)
        history = json.loads(my_user.history)
        new_hist = {'query': query,
                    'datetime': datetime.now().strftime('%m/%d/%Y, %H:%M:%S'),
                    'results': passages}
        history.append(new_hist)
        my_user.history = json.dumps(history)
        my_user.save()
        #print(f'User: {user.username}')
        #print(f'History: {json.dumps(history, indent=2)}')    
        
    return render(request, os.getcwd() + "/capstone/templates/results.html", context)

def user_profile(request):
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user.username)
        my_user = models.User.objects.get(user=user)
        history = json.loads(my_user.history)
        history.reverse() # because of ordering

        results_cat = ""
        for p in history:
            for r in p['results']['SCI']:
                results_cat += r[0]
        related_supps = related_links.get_related_supplements(results_cat)

        context = {'history': history, 'related_supps': related_supps}
        return render(request, os.getcwd() + '/capstone/templates/user_profile.html', context)
    else:
        return redirect('/')

def emotion(request):
    if request.method == "POST":
        text = request.POST.get("some_shit")
        try:
            return HttpResponse(json.dumps(get_emotion(text)))
        except Exception as e:
            print(e.message)
            return HttpResponse(json.dumps({"error": e.message}))
    else:
        return HttpResponse(
            json.dumps(
                {"message": "error", "error": "must do POST request for /emotion/"}
            )
        )


def entity(request):
    if request.method == "POST":
        text = request.POST.get("some_shit")
        try:
            return HttpResponse(json.dumps(get_entity(text)))
        except Exception as e:
            print(e.message)
            return HttpResponse(json.dumps({"error": e.message}))
    else:
        return HttpResponse(json.dumps({"message": "entity error"}))
