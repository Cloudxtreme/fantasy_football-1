import logging
import os
import random
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from glass import oauth_utils
from glass.mirror import Mirror
from models import GoogleCredential, UserProfile, League, UserLeague


logger = logging.getLogger('website')
client_secrets_filename = os.path.join(
    settings.PROJECT_ROOT, 'client_secrets.json')


def homepage(request):
    """
    Decide where to send user based on whether they are logged in or not.
    """
    template_data = {}
    logger.debug("User id: {0}".format(request.user.username))
    if not request.user.is_authenticated():
        template_data['auth_url'] = oauth_utils.get_auth_url(request, client_secrets_filename=client_secrets_filename, redirect_uri=settings.GOOGLE_REDIRECT_URI)
        return render_to_response('landing.html', template_data, context_instance=RequestContext(request))
    return dashboard(request)


def dashboard(request):
    template_data = {}
    template_data['user_id'] = request.user.id
    return render_to_response('dashboard.html', template_data, context_instance=RequestContext(request))


def oauth_return(request):
    if not request.user.is_authenticated():
        # Create a new user automagically.
        user = User()
        user.username = '%030x' % random.randrange(16**30)
        # password = '%030x' % random.randrange(16**30)
        user.set_unusable_password()
        user.save()
        # authenticate(username=user.username)
        user.backend='django.contrib.auth.backends.ModelBackend'
        login(request, user)
        # Now we need to create a user profile and an initial league.
        # TODO let the user create the league. And have multiple leagues.
        league = League()
        league.save()
        user_profile = UserProfile()
        user_profile.user = user
        user_profile.save()
        ul = UserLeague(league=league, user_profile=user_profile)
        ul.save()
    return oauth_utils.process_oauth_redirect(request, client_secrets_filename=client_secrets_filename, redirect_uri=settings.GOOGLE_REDIRECT_URI)
