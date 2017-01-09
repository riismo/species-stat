"""Views


Copyright 2017 Riismo

This file is part of species-stat.

species-stat is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

species-stat is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
species-stat.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import urllib.parse
import logging

import requests_oauthlib

import django.http
import django.template
import django.core.urlresolvers
import django.views.decorators.http

from . import forms
from . import models
from . import decorators

TWITTER_CLIENT_KEY = 'invalid'
TWITTER_CLIENT_SECRET = 'invalid'
with open('..' + os.sep + 'keys' + os.sep + 'twitter_secret.py', 'r') as key:
    exec(key.read())  # pylint: disable=locally-disabled,exec-used

LOGGER = logging.getLogger(__name__)


@django.views.decorators.http.require_safe
@decorators.prohibit_invalid_user
def index(request):
    """Main landing page, explaining project and offering navigation
    """
    template = django.template.loader.get_template('survey/index.html')
    context = {
        'authenticated': request.user is not None,
        'userinfo_url': django.core.urlresolvers.reverse_lazy('userinfo'),
        'responses_url': django.core.urlresolvers.reverse_lazy('survey'),
        'login_url': django.core.urlresolvers.reverse_lazy('login'),
        'logout_url': django.core.urlresolvers.reverse_lazy('logout'),
    }

    if request.user is not None:
        context['username'] = request.user.username
        context['icon_url'] = request.user.icon_url
        context['has_userinfo'] = request.user.userinfo_is_complete()
        context['pending_responses'] = request.user.pending_response_count()
        context['has_pending'] = (request.user.pending_response_count() != 0)
        context['answered_responses'] = request.user.answered_response_count()
        context['has_answered'] = (request.user.answered_response_count() != 0)
        context['view_url'] = django.core.urlresolvers.reverse_lazy(
            'view',
            args=[request.user.result_id.hex])

    return django.http.HttpResponse(template.render(context, request))


@django.views.decorators.http.require_safe
def logout(request):
    """End the current session and redirect back to the main page
    """
    request.session.flush()
    return django.http.HttpResponseRedirect(
        django.core.urlresolvers.reverse_lazy('welcome'))


@django.views.decorators.http.require_safe
def login(request):
    """Initiate login with Twitter
    """
    request.session.flush()
    request_token_url = u'https://api.twitter.com/oauth/request_token'

    oauth = requests_oauthlib.OAuth1Session(
        TWITTER_CLIENT_KEY,
        client_secret=TWITTER_CLIENT_SECRET)
    response = oauth.fetch_request_token(request_token_url)
    request.session['user_oa_key'] = response.get('oauth_token')
    request.session['user_oa_secret'] = response.get('oauth_token_secret')

    base_authorization_url = u'https://api.twitter.com/oauth/authorize'

    authorization_url = oauth.authorization_url(base_authorization_url)
    return django.http.HttpResponseRedirect(authorization_url)


@django.views.decorators.http.require_safe
def login_callback(request):
    """Redirected here from Twitter OAuth, verify info and (if new) set up user
    """
    oauth = requests_oauthlib.OAuth1Session(
        TWITTER_CLIENT_KEY,
        client_secret=TWITTER_CLIENT_SECRET)
    fake_redirect = (
        'https://localhost/fake_callback?oauth_token={}&oauth_verifier={}'
        .format(urllib.parse.quote(request.GET['oauth_token']),
                urllib.parse.quote(request.GET['oauth_verifier'])))
    oauth_response = oauth.parse_authorization_response(fake_redirect)

    verifier = oauth_response.get('oauth_verifier')

    access_token_url = 'https://api.twitter.com/oauth/access_token'
    user_key = request.session['user_oa_key']
    user_secret = request.session['user_oa_secret']
    oauth = requests_oauthlib.OAuth1Session(
        TWITTER_CLIENT_KEY,
        client_secret=TWITTER_CLIENT_SECRET,
        resource_owner_key=user_key,
        resource_owner_secret=user_secret,
        verifier=verifier)
    oauth_tokens = oauth.fetch_access_token(access_token_url)
    request.session['user_oa_key'] = oauth_tokens.get('oauth_token')
    request.session['user_oa_secret'] = oauth_tokens.get('oauth_token_secret')

    profile_url = ('https://api.twitter.com/1.1/account/'
                   'verify_credentials.json'
                   '?include_entities=false'
                   '&skip_status=true'
                   '&include_email=false')

    oauth_request = oauth.get(profile_url)
    if oauth_request.status_code != 200:
        request.session.flush()
        return django.http.HttpResponseForbidden()

    payload = oauth_request.json()
    user = models.User.get_or_create_user(
        payload['screen_name'],
        payload.get('profile_image_url_https', ''))

    if user.total_response_count() == 0:
        user.load_friends(oauth)

    request.session['validated_username'] = user.username

    next_page = django.core.urlresolvers.reverse_lazy('welcome')
    if user.species is None:
        next_page = django.core.urlresolvers.reverse_lazy('userinfo')
    elif user.pending_response_count() > 0:
        next_page = django.core.urlresolvers.reverse_lazy('survey')
    elif user.answered_response_count() > 0:
        next_page = django.core.urlresolvers.reverse_lazy(
            'view',
            kwargs={'result_id': user.result_id.hex})
    return django.http.HttpResponseRedirect(next_page)


@decorators.require_valid_user(
    fail_redirect=django.core.urlresolvers.reverse_lazy('welcome'))
def userinfo(request):
    """The initial survey setup
    """
    if request.user.userinfo_is_complete():
        return django.http.HttpResponseRedirect(
            django.core.urlresolvers.reverse_lazy('welcome'))

    form = None

    if request.method == 'POST':
        form = forms.UserinfoForm(request.POST)

        if not form.is_valid():
            print(form)

        if form.is_valid():
            species = form.cleaned_data.get('species')
            species_custom = form.cleaned_data.get('species_custom')

            if species_custom is not None and len(species_custom) == 0:
                species_custom = None
            request.user.set_userinfo(species,
                                      species_custom=species_custom)
            return django.http.HttpResponseRedirect(
                django.core.urlresolvers.reverse_lazy('survey'))

    if form is None:
        form = forms.UserinfoForm(username=request.user.username,
                                  icon_url=request.user.icon_url)

    template = django.template.loader.get_template('survey/userinfo.html')

    context = {
        'form': form,
    }
    return django.http.HttpResponse(template.render(context, request))


@django.views.decorators.http.require_safe
@decorators.require_valid_user(
    fail_redirect=django.core.urlresolvers.reverse_lazy('welcome'))
def survey(request):
    """The main survey form
    """
    friends = {}
    pending_responses = (models.Response.objects
                         .filter(source=request.user)
                         .filter(species=None))
    for response in pending_responses:
        friends[response.target.username] = response.target.icon_url

    form = forms.SurveyForm(friends=friends)

    template = django.template.loader.get_template('survey/survey.html')
    context = {
        'form': form,
    }
    return django.http.HttpResponse(template.render(context, request))


@django.views.decorators.http.require_POST
@decorators.require_valid_user()
def complete(request):
    """Survey processing; redirects to appropriate view page
    """
    form = forms.SurveyForm(request.POST)

    if not form.is_valid():
        return django.http.HttpResponseBadRequest()

    friend_prefix = 'friend_'
    for field, answer in form.cleaned_data.items():
        if not field.startswith(friend_prefix):
            continue

        if answer == '':
            continue

        try:
            target = models.User.objects.get(
                username=field[len(friend_prefix):])
        except models.User.DoesNotExist:
            return django.http.HttpResponseBadRequest()

        try:
            response = models.Response.objects.get(source=request.user,
                                                   target=target)
        except models.Response.DoesNotExist:
            return django.http.HttpResponseBadRequest()

        try:
            species = models.Species.objects.get(name=answer)
        except models.Species.DoesNotExist:
            return django.http.HttpResponseBadRequest()

        response.species = species
        response.save()
    return django.http.HttpResponseRedirect(
        django.core.urlresolvers.reverse_lazy(
            'view',
            args=[request.user.result_id.hex]))


@django.views.decorators.http.require_safe
@decorators.prohibit_invalid_user
@decorators.require_valid_result_id
def view_result(request):
    """View the results for anyone you know the result_id of
    """
    template = django.template.loader.get_template('survey/complete.html')

    context = {
        'own_results': request.result_user == request.user,
        'root_url': django.core.urlresolvers.reverse_lazy('welcome'),
        'summary_username': request.result_user.username,
        'summary_icon_url': request.result_user.icon_url,
        'summary': request.result_user.result_summary(),
        'logout_url': django.core.urlresolvers.reverse_lazy('logout'),
    }

    return django.http.HttpResponse(template.render(context, request))
