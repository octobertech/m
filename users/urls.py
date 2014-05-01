from django.conf.urls import patterns, url

urlpatterns = patterns('users.views',
    url('^login/$', 'login', name='login'),
    url('^signup/$', 'signup', name='signup'),
    url('^settings/$', 'settings', name='settings'),
    url('^logout/$', 'logout', name='logout'),
    url(r'^find-users/$', 'find_users', name='find_users'),
    url(r'^modify-user/$', 'modify_user', name='modify_user'),
)
