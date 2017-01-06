"""Survey urls


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

import django.conf.urls

from . import views

urlpatterns = [  # pylint: disable=locally-disabled,invalid-name
    django.conf.urls.url(r'^$',
                         views.index,
                         name='welcome'),

    django.conf.urls.url(r'^login/$',
                         views.login,
                         name='login'),

    django.conf.urls.url(r'^logout/$',
                         views.logout,
                         name='logout'),

    django.conf.urls.url(r'^login_callback/$',
                         views.login_callback,
                         name='login_callback'),

    django.conf.urls.url(r'^userinfo/$',
                         views.userinfo,
                         name='userinfo'),

    django.conf.urls.url(r'^responses/$',
                         views.survey,
                         name='survey'),

    django.conf.urls.url(r'^complete/$',
                         views.complete,
                         name='complete'),

    django.conf.urls.url(r'^view/(?P<result_id>[a-z0-9]{32})$',
                         views.view_result,
                         name='view'),
]
