"""Models


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

import uuid

import django.db
from . import choices


NOTHING_SPECIES = 'nothing'
OTHER_SPECIES = 'other'


class User(django.db.models.Model):
    """A Twitter user either taking the survey or referenced by one who is
    """
    username = django.db.models.CharField(max_length=16,
                                          primary_key=True)
    icon_url = django.db.models.CharField(max_length=256)
    result_id = django.db.models.UUIDField(default=uuid.uuid4, editable=False)
    species = django.db.models.ForeignKey('Species',
                                          on_delete=django.db.models.CASCADE,
                                          null=True)
    species_custom = django.db.models.CharField(max_length=256,
                                                null=True)

    def userinfo_is_complete(self):
        """Return whether the initial userinfo has been registered.
        """
        return self.species is not None

    def set_userinfo(self, species_id, species_custom=None):
        """Register the initial userinfo.
        """
        if species_id == OTHER_SPECIES and species_custom is None:
            raise ValueError('Missing species_custom')

        species = Species.objects.get(name=species_id)
        self.species = species
        if species_id == OTHER_SPECIES:
            self.species_custom = species_custom

        self.save()

    def result_summary(self):
        """Return summary data for this user's responses, ready to graph.
        """
        responses = Response.objects.filter(source=self).exclude(species=None)

        total_count = 0
        species_count = {}
        for k, _ in choices.CHOICES:
            if k != NOTHING_SPECIES:
                species_count[k] = 0

        for response in responses:
            if response.species.name in species_count:
                species_count[response.species.name] += 1
                total_count += 1

        divisor = total_count if total_count else 1

        species_pct = {}
        for species, count in species_count.items():
            species_pct[species] = (1.0*count) / divisor

        deltas = list()
        for category in choices.CATEGORIES:
            for choice in category.choices:
                if choice.percentage is not None and choice.percentage > 0:
                    deltas.append((choice.pretty_name,
                                   ((1.0*species_pct.get(choice.name, 0.0)) /
                                    choice.percentage),
                                   species_pct.get(choice.name, 0.0),
                                   choice.percentage))

        deltas.sort(key=lambda x: x[1], reverse=True)

        return {
            'deltas': deltas,
            'text_summary': self.__text_summary(deltas),
        }

    def __text_summary(self, deltas):
        max_notes = 3

        if len(deltas) < 1:
            return ('{} did not name any following species.'
                    .format(self.username))
        else:
            summary_header = ("{}'s follow list has "
                              .format(self.username))
            notes = []
            for i in range(len(deltas)
                           if len(deltas) <= max_notes
                           else max_notes):
                notes.append(
                    '{:.0f}% the normal amount of {}'
                    .format(deltas[i][1]*100.0, deltas[i][0].lower()))

            notes[-1] = 'and ' + notes[-1]
        return summary_header + ', '.join(notes) + '.'

    def answered_response_count(self):
        """Return number of responses this user has answered.
        """
        return (Response.objects
                .filter(source=self)
                .exclude(species=None)
                .count())

    def pending_response_count(self):
        """Return number of unanswered responses this user has available.
        """
        return (Response.objects
                .filter(source=self)
                .filter(species=None)
                .count())

    def total_response_count(self):
        """Return total answered and unanswered responses from this user.
        """
        return (Response.objects
                .filter(source=self)
                .count())

    @classmethod
    def get_or_create_user(cls, target, icon_url):
        """Return specified user, creating first if required.
        """
        try:
            user = cls.objects.get(username=target)
        except cls.DoesNotExist:
            user = cls(username=target, icon_url=icon_url)
            user.save()

        return user

    def __ensure_response_exists(self, target_name, icon_url):
        """Return specified response, creating first if required.
        """
        target_user = self.get_or_create_user(target_name, icon_url)

        try:
            response = Response.objects.get(source=self, target=target_user)
        except Response.DoesNotExist:
            response = Response(source=self, target=target_user)
            response.save()

    def load_friends(self, session):
        """Load user's twitter follow list, using provided oauth session.
        """
        max_pages = 5  # Arbitrarily chose 200x5 max friends

        friends_url_format = ('https://api.twitter.com/1.1/friends/list.json'
                              '?screen_name={}'
                              '&cursor={}'
                              '&count=200'
                              '&skip_status=true'
                              '&include_user_entities=false')

        cursor = -1
        for _ in range(max_pages):
            if cursor == 0:
                break

            response = session.get(
                friends_url_format.format(self.username, cursor))
            if response.status_code != 200:
                response.raise_for_status()

            payload = response.json()
            cursor = payload['next_cursor']
            for friend in payload['users']:
                self.__ensure_response_exists(
                    friend['screen_name'],
                    friend['profile_image_url_https'])

        self.save()


class Species(django.db.models.Model):
    """A species known to the database as a valid survey response
    """
    name = django.db.models.CharField(max_length=32, primary_key=True)
    pretty_name = django.db.models.CharField(max_length=64)


class Response(django.db.models.Model):
    """A single survey response, one user declaring the species of one user
    """
    source = django.db.models.ForeignKey(User,
                                         on_delete=django.db.models.CASCADE,
                                         related_name='+')
    target = django.db.models.ForeignKey(User,
                                         on_delete=django.db.models.CASCADE,
                                         related_name='+')
    species = django.db.models.ForeignKey(Species,
                                          on_delete=django.db.models.CASCADE,
                                          null=True)

    class Meta:
        unique_together = (('source', 'target'),)
