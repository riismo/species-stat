"""Initial handling of fixed species options and their statistics

This might be nicer handled entirely as part of the db, which then
allows fun runtime changes like also giving stats compared to previous
responses.


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


# pylint: disable=locally-disabled,too-few-public-methods
class SpeciesCategory(object):
    """A grouping of several species, mainly for display purposes
    """
    def __init__(self, name, pretty_name, choices):
        self.name = name
        self.pretty_name = pretty_name
        self.choices = choices
        self.frequency = None
        self.percentage = None


# pylint: disable=locally-disabled,too-few-public-methods
class SpeciesChoice(object):
    """A single species, with display and baseline statistical info
    """
    def __init__(self, name, pretty_name, frequency):
        self.name = name
        self.pretty_name = pretty_name
        self.frequency = frequency
        self.percentage = None


def __generate_choices(categories):
    retval = list()

    for category in categories:
        for choice in category.choices:
            retval.append((choice.name, choice.pretty_name))

    return tuple(retval)


def __generate_choice_categories(categories):
    retval = {}

    for category in categories:
        for choice in category.choices:
            retval[choice.name] = (category.name, category.pretty_name)

    return retval


def __generate_percentages(categories):
    total_frequency = 0
    for category in categories:
        category.frequency = 0
        for choice in category.choices:
            category.frequency += choice.frequency
            total_frequency += choice.frequency

    if total_frequency <= 0:
        raise Exception('Invalid frequency data in choices')

    for category in categories:
        category.percentage = (1.0*category.frequency) / total_frequency
        for choice in category.choices:
            choice.percentage = (1.0*choice.frequency) / total_frequency


def choice_category(choicename):
    """Return the SpeciesCategory containing specified choice name.
    """
    return __CHOICECATEGORIES.get(choicename, ('unknown', 'Unknown'))


def choice_percent(choicename):
    """Return the baseline percentage for the specified choice name.
    """
    return __CHOICECATEGORIES.get(choicename, 'unknown')


# data from http://vis.adjectivespecies.com/furrysurvey/explorer/
# using 2015 results only
CATEGORIES = (
    SpeciesCategory(name='vulpini', pretty_name='yip', choices=(
        SpeciesChoice('redfox', 'Red Fox', 1018),
        SpeciesChoice('arcticfox', 'Arctic Fox', 354),
        SpeciesChoice('greyfox', 'Grey Fox', 202),
        SpeciesChoice('kitsune', 'Kitsune', 320),
        SpeciesChoice('otherfox', 'Other Fox', 521),
    )),
    SpeciesCategory(name='canidae', pretty_name='woof', choices=(
        SpeciesChoice('germanshepherd', 'German Shepherd', 282),
        SpeciesChoice('husky', 'Husky', 758),
        SpeciesChoice('otherdog', 'Other Dog', 716),
        SpeciesChoice('coyote', 'Coyote', 247),
        SpeciesChoice('wolf', 'Wolf', 2672),
        SpeciesChoice('othercanine', 'Other Canid', 311),
    )),
    SpeciesCategory(name='felidae', pretty_name='meow', choices=(
        SpeciesChoice('domesticcat', 'Domestic Cat', 790),
        SpeciesChoice('tiger', 'Tiger', 430),
        SpeciesChoice('lion', 'Lion', 295),
        SpeciesChoice('cheetah', 'Cheetah', 147),
        SpeciesChoice('panther', 'Panther', 125),
        SpeciesChoice('leopard', 'Leopard', 117),
        SpeciesChoice('otherfeline', 'Other Felid', 542),
    )),
    SpeciesCategory(name='othermammal', pretty_name='sound', choices=(
        SpeciesChoice('hyaena', 'Hyena', 207),
        SpeciesChoice('raccoon', 'Raccoon', 261),
        SpeciesChoice('riverotter', 'River Otter', 216),
        SpeciesChoice('rabbit', 'Rabbit', 367),
        SpeciesChoice('bat', 'Bat', 211),
        SpeciesChoice('horse', 'Horse', 255),
    )),
    SpeciesCategory(name='othernonmammal', pretty_name='othersound', choices=(
        SpeciesChoice('raven', 'Raven', 119),
        SpeciesChoice('otherbird', 'Other Avian', 229),
        SpeciesChoice('kangaroo', 'Kangaroo', 117),
        SpeciesChoice('lizard', 'Lizard', 186),
        SpeciesChoice('dragon', 'Dragon', 1268),
        SpeciesChoice('griffin', 'Griffin', 152),
    )),
    SpeciesCategory(name='other', pretty_name='other', choices=(
        SpeciesChoice('other', 'Other', 1815),
    )),
    SpeciesCategory(name='nothing', pretty_name='silence', choices=(
        SpeciesChoice('nothing', 'No Species', 0),
    )),
)


CHOICES = __generate_choices(CATEGORIES)
__CHOICECATEGORIES = __generate_choice_categories(CATEGORIES)
__generate_percentages(CATEGORIES)
