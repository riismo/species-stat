"""Decorators


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

import django.core.exceptions
import django.http

from . import models


def require_valid_user(fail_redirect=None):
    """Require the wrapped request includes a valid user (and add the object).

    If no user is set on the current session, it will redirect to fail_redirect
    if set and raise PermissionDenied otherwise.

    If an invalid user is set on the current session (which should never be
    possible), it raises SuspiciousOperation.

    """
    def __require_valid_user(function):
        def __wrap(request, *args, **kwargs):
            username = request.session.get('validated_username')
            if username is None:
                if fail_redirect is None:
                    raise django.core.exceptions.PermissionDenied(
                        'Valid user required')
                else:
                    return django.http.HttpResponseRedirect(fail_redirect)

            try:
                user = models.User.objects.get(username=username)
            except models.User.DoesNotExist:
                request.session.flush()
                raise django.core.exceptions.SuspiciousOperation(
                    'Invalid user')

            request.user = user
            return function(request, *args, **kwargs)

        __wrap.__doc__ = function.__doc__
        __wrap.__name__ = function.__name__
        return __wrap

    return __require_valid_user


def prohibit_invalid_user(function):
    """Require the request's user is valid (if present) and add the object.

    If an invalid user is set on the current session (which should never be
    possible), it raises SuspiciousOperation.

    """
    def __wrap(request, *args, **kwargs):
        username = request.session.get('validated_username')
        if username is None:
            request.user = None
        else:
            try:
                user = models.User.objects.get(username=username)
            except models.User.DoesNotExist:
                request.session.flush()
                raise django.core.exceptions.SuspiciousOperation(
                    'Invalid user')

            request.user = user

        return function(request, *args, **kwargs)

    __wrap.__doc__ = function.__doc__
    __wrap.__name__ = function.__name__
    return __wrap


def require_valid_result_id(function):
    """Require the arguments include a valid request_id (and consume it).

    If no result_id is set (due to calling error), it raises ValueError.

    If an invalid request_id is set (for instance due to a user changing the
    requested url), it raises SuspiciousOperation.
    """
    def __wrap(request, result_id=None, *args, **kwargs):
        if result_id is None:
            raise ValueError('Missing result_id')
        try:
            result_user = models.User.objects.get(result_id=result_id)
        except models.User.DoesNotExist:
            raise django.core.exceptions.SuspiciousOperation(
                'Invalid result id')

        request.result_user = result_user
        return function(request, *args, **kwargs)

    __wrap.__doc__ = function.__doc__
    __wrap.__name__ = function.__name__
    return __wrap
