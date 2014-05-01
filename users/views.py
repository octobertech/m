from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from forms import LoginForm, RegistrationForm, SettingsForm

from mikiapp import models

def login(request):
    login_form = LoginForm()
    next = request.REQUEST.get('next')
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.get_username()
            request.session['username'] = username
            if next:
                return HttpResponseRedirect(next)
            return HttpResponseRedirect('/')

    context = {
        'login_form': login_form,
        'next': next,
    }
    return render_to_response('login.html', context,
        context_instance=RequestContext(request))

def signup(request):
    register_form = RegistrationForm()
    next = request.REQUEST.get('next')
    if request.method == 'POST':
        register_form = RegistrationForm(request.POST)
        if register_form.is_valid():
            username = register_form.save()
            request.session['username'] = username
            if next:
                return HttpResponseRedirect(next)
            return HttpResponseRedirect('/')

    context = {
        'register_form': register_form,
        'next': next,
    }
    return render_to_response('signup.html', context,
        context_instance=RequestContext(request))

def settings(request):
    settings_form = SettingsForm()
    next = request.REQUEST.get('next')
    if request.method == 'POST':
        settings_form = SettingsForm(request.POST)
        if settings_form.is_valid():
            username = settings_form.save()
            request.session['username'] = username
            if next:
                return HttpResponseRedirect(next)
            return HttpResponseRedirect('/')

    context = {
        'settings_form': settings_form,
        'next': next,
    }
    return render_to_response('settings.html', context,
        context_instance=RequestContext(request))



def logout(request):
    request.session.pop('username', None)
    return HttpResponseRedirect('/')


def find_users(request):
    reading_usernames = []
    if request.user['is_authenticated']:
        reading_usernames = models.get_reading_usernames(request.session['username']) + [request.session['username']]
    q = request.GET.get('q')
    result = None
    searched = False
    if q is not None:
        searched = True
        try:
            result = models.get_user_by_username(q)
            result['reading'] = q in reading_usernames
        except models.DatabaseError:
            pass
    context = {
        'q': q,
        'result': result,
        'searched': searched,
        'reading_usernames': reading_usernames,
    }
    return render_to_response('find_users.html', context,
        context_instance=RequestContext(request))

def modify_user(request):
    next = request.REQUEST.get('next')
    readed = False
    unreaded = False
    if request.user['is_authenticated']:
        if 'read' in request.POST:
            models.read(request.session['username'], [request.POST['read']])
            readed = True
        if 'unread' in request.POST:
            models.unread(request.session['username'], request.POST['unread'])
            unreaded = True
    if next:
        return HttpResponseRedirect(next)
    context = {
        'readed': readed,
        'unreaded': unreaded,
    }
    return render_to_response('modify_user.html', context,
        context_instance=RequestContext(request))


