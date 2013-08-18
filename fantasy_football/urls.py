from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'fantasy_football.views.home', name='home'),
    # url(r'^fantasy_football/', include('fantasy_football.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

)

urlpatterns += patterns('website.views',
    url(r'^$', 'homepage'),
    # url(r'^oauth2callback/$', 'callback'),
    url(r'^oauth/google/redirect/$', 'oauth_return'),


)

urlpatterns += patterns('website.api',
    url(r'^api/scores/$', 'scores'),
    url(r'^api/scores/(?P<user_id>\d+)/$', 'scores'),
    url(r'^api/players/', 'players')
)
