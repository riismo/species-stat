"""Forms


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

import django.forms
import django.utils.encoding
import django.utils.html
import django.utils.safestring

from . import choices
from . import models


# pylint: disable=locally-disabled,too-few-public-methods
class SpeciesRenderer(django.forms.widgets.RadioFieldRenderer):
    """Custom RadioFieldRenderer with species categories
    """
    outer_html = '<div{id_attr} class="speciesfield">{content}</div>'
    cat_begin_html = '<div class="speciescategory {cat_name}">'
    cat_end_html = '</div>'
    inner_html = '<div>{choice_value}{sub_widgets}</div>'

    def render(self):
        """
        Outputs a <ul> for this set of choice fields.
        If an id was given to the field, it is applied to the <ul> (each
        item in the list will get an id of `$id_$i`).
        """
        id_ = self.attrs.get('id')
        output = []
        prev_category = None
        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            cat_name, cat_label = (
                choices.choice_category(choice_value))
            if cat_name != prev_category:
                if prev_category is not None:
                    output.append(
                        django.utils.html.format_html(self.cat_end_html))
                output.append(
                    django.utils.html.format_html(self.cat_begin_html,
                                                  cat_name=cat_name,
                                                  cat_label=cat_label))
                prev_category = cat_name
            if isinstance(choice_label, (tuple, list)):
                attrs_plus = self.attrs.copy()
                if id_:
                    attrs_plus['id'] += '_{}'.format(i)
                sub_ul_renderer = self.__class__(
                    name=self.name,
                    value=self.value,
                    attrs=attrs_plus,
                    choices=choice_label,
                )
                sub_ul_renderer.choice_input_class = self.choice_input_class
                output.append(django.utils.html.format_html(
                    self.inner_html, choice_value=choice_value,
                    sub_widgets=sub_ul_renderer.render(),
                ))
            else:
                widget = self.choice_input_class(self.name,
                                                 self.value,
                                                 self.attrs.copy(),
                                                 choice,
                                                 i)
                output.append(
                    django.utils.html.format_html(
                        self.inner_html,
                        choice_value=django.utils.encoding.force_text(widget),
                        sub_widgets=''))
        if prev_category is not None:
            output.append(django.utils.html.format_html(self.cat_end_html))
            prev_category = None

        return django.utils.html.format_html(
            self.outer_html,
            id_attr=(django.utils.html.format_html(' id="{}"', id_)
                     if id_
                     else ''),
            content=django.utils.safestring.mark_safe('\n'.join(output)),
        )


class SpeciesSelect(django.forms.widgets.RadioSelect):
    """Custom RadioSelect using the SpeciesRenderer renderer
    """
    renderer = SpeciesRenderer


class SpeciesField(django.forms.ChoiceField):
    """Custom ChoiceField using the SpeciesSelect widget

    This saves the icon url associated with the field for later template use.
    """
    widget = SpeciesSelect
    default_choices = choices.CHOICES

    def __init__(self, *args, **kwargs):
        if not hasattr(kwargs, 'choices'):
            kwargs['choices'] = self.default_choices
        self.icon_url = kwargs.pop('icon_url')

        super(SpeciesField, self).__init__(*args, **kwargs)


class SurveyForm(django.forms.Form):
    """Primary form for the follower species survey
    """
    friendlist = django.forms.CharField(widget=django.forms.HiddenInput())
    baseline_species_percent = {}

    for category in choices.CATEGORIES:
        for choice in category.choices:
            if choice.percentage is not None and choice.percentage > 0:
                baseline_species_percent[choice.name] = choice.percentage

    @staticmethod
    def __parse_friends(friendstr):
        retval = {}
        for friend in friendstr.split(','):
            retval[friend] = ''

        return retval

    def __init__(self, *args, **kwargs):
        friends = kwargs.pop('friends', None)

        if friends is None and len(args) > 0:
            friendlist = args[0].get('friendlist', None)
            if friendlist is not None:
                friends = SurveyForm.__parse_friends(friendlist)

        super(SurveyForm, self).__init__(*args, **kwargs)

        self.fields['friendlist'].initial = ','.join(friends.keys())

        for username, url in friends.items():
            self.fields['friend_%s' % username] = (
                SpeciesField(label=username, icon_url=url, required=False))


class UserinfoForm(django.forms.Form):
    """Primary form for the follower species survey
    """
    species_custom = django.forms.CharField(required=False,
                                            label='Species (if "other")')
    username = django.forms.CharField(widget=django.forms.HiddenInput())
    icon_url = django.forms.CharField(widget=django.forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        username = kwargs.pop('username', None)
        icon_url = kwargs.pop('icon_url', None)

        if len(args) > 0:
            if username is None:
                username = args[0].get('username', None)
            if icon_url is None:
                icon_url = args[0].get('icon_url', None)

        if username is None:
            raise ValueError('No username set')
        if icon_url is None:
            raise ValueError('No icon_url set')

        super(UserinfoForm, self).__init__(*args, **kwargs)

        self.fields['username'].initial = username
        self.fields['icon_url'].initial = icon_url

        self.fields['species'] = (
            SpeciesField(label=username, icon_url=icon_url, required=True))
        self.order_fields(['species', 'species_custom'])

    def clean(self):
        cleaned_data = super(UserinfoForm, self).clean()
        species = cleaned_data.get('species')
        species_custom = cleaned_data.get('species_custom')

        if species == models.OTHER_SPECIES:
            if species_custom is None or len(species_custom) < 1:
                raise django.forms.ValidationError(
                    'Custom species must be entered if "other" is selected.')
