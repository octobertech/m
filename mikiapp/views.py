from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse

from forms import MikiForm

import models


NUM_PER_PAGE = 40

def timeline(request):
    form = MikiForm()
    if request.user['is_authenticated'] and request.method == "POST":
        form = MikiForm(request.POST)
        if form.is_valid():
            models.save_miki(request.session['username'], form.cleaned_data['body'])
            return HttpResponseRedirect(reverse('timeline'))
    else:
        start = request.GET.get('start')
        if request.user['is_authenticated']:
            mikis, next = models.get_timeline(request.session['username'],
            start=start, limit=NUM_PER_PAGE)
        else:
            mikis, next = models.get_timeline(models.PUBLIC_TIMELINE_KEY, start=start,
            limit=NUM_PER_PAGE)
    context = {
        'form': form,
        'mikis': mikis,
        'next': next,
    }
    return render_to_response('timeline.html', context,
        context_instance=RequestContext(request))

def publicline(request):
    start = request.GET.get('start')
    mikis,next = models.get_timeline(models.PUBLIC_TIMELINE_KEY, start=start,
        limit=NUM_PER_PAGE)

    context = {
        'mikis': mikis,
        'next': next,
    }
    return render_to_response('publicline.html', context,
        context_instance=RequestContext(request))

def userline(request, username):
    try:
        user = models.get_user_by_username(username)
    except models.DatabaseError:
        raise Http404

    # Query for the reading users ids
    reading_usernames = []
    if request.user['is_authenticated']:
        reading_usernames = models.get_reading_usernames(username)

    # Adds a property on the user to indicate whether the currently
    # logged in user is reading some user
    user['reading'] = username in reading_usernames

    if request.user['is_authenticated'] and request.method == "POST":
        if user['reading']:
            models.unread(request.session['username'], username)
        else:
            models.read(request.session['username'], username)

        return HttpResponseRedirect(reverse('timeline'))


    start = request.GET.get('start')

    mikis, next = models.get_userline(username, start=start, limit=NUM_PER_PAGE)

    #profile = models.get_profile(username)

    context = {
        'user': user,
        'username': username,
        #'profile': profile,
        'mikis': mikis,
        'next': next,
        'reading_usernames': reading_usernames,
    }
    return render_to_response('userline.html', context,
        context_instance=RequestContext(request))

def compose_miki(request):
    form = MikiForm()
    if request.user['is_authenticated'] and request.method == "POST":
        form = MikiForm(request.POST)
        if form.is_valid():
            models.save_miki(request.session['username'], form.cleaned_data['body'])
            return HttpResponseRedirect(reverse('timeline'))

    context = {}
    return render_to_response('compose_miki.html', context,
        context_instance=RequestContext(request))

def search(request):
    q = request.GET.get('q')
    result = None
    searched = False
    if q is not None:
        searched = True
        #try:

        #except:
        #    pass

    context = {
        'q': q,
        'result': result,
        'searched': searched,
    }

    return render_to_response('search.html', context,
                              context_instance=RequestContext(request))

