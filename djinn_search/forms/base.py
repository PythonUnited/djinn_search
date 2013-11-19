import logging
from django import forms
from haystack.forms import SearchForm as Base
from haystack.constants import DJANGO_CT
from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet
from djinn_contenttypes.registry import CTRegistry
from pgsearch.utils import remove_punctuation, split_query


class BaseSearchForm(Base):

    """ Base form for Djinn search. This always takes the user into
    account, to be able to check on allowed content. """

    # Tainted marker for default 'AND' that has been reinterpreted as 'OR',
    #
    and_or_tainted = False

    def __init__(self, *args, **kwargs):

        self.user = kwargs['user']
        del kwargs['user']

        return super(BaseSearchForm, self).__init__(*args, **kwargs)

    def search(self):

        if not self.is_valid():
            return self.no_query_found()

        if not self.cleaned_data.get('q'):
            return self.no_query_found()

        sqs = SearchQuerySet()
        sqs = sqs.filter(content=AutoQuery(self.cleaned_data['q']))

        return sqs

    def _detect_and_or(self, sqs):

        # let's see whether we have something useful. If not, we'll
        # try the separate query parts that are regular words and go for an
        # (OR query).
        #
        parts = split_query(self.cleaned_data['q'], sqs.query)

        if not sqs.count() and len(parts) > 1:

            self.and_or_tainted = True

            sqs = SearchQuerySet()
            sqs = sqs.filter(content=parts[0])

            for part in parts[1:]:
                sqs = sqs.filter_or(content=part)

        return sqs

    def _filter_allowed(self, sqs):
        
        """ Do check on allowed users on all content in the set """

        access_to = ['group_users', 'user_%s' % self.user.username]

        for group in self.user.usergroup_set.all():
            access_to.append('group_%d' % group.id)

        sqs = sqs.filter(allow_list__in=access_to)

        return sqs


class SearchForm(BaseSearchForm):

    """ Default implementation """
