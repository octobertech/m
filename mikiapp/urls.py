from django.conf.urls import patterns, url

urlpatterns = patterns('mikiapp.views',
    url(r'^/?$', 'timeline', name='timeline'),
    url(r'^search/$', 'search', name='search'),
    url(r'^public/$', 'publicline', name='publicline'),
    url(r'^compose_miki/$', 'compose_miki', name='compose_miki'),
    url(r'^(?P<username>\w+)/$', 'userline', name='userline'),


)
