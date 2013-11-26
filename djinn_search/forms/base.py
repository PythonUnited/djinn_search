from django.conf import settings
from haystack.forms import SearchForm as Base
from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet
from haystack.constants import DJANGO_CT
from djinn_search.utils import split_query
from djinn_search.fields.contenttype import CTField


class BaseSearchForm(Base):

    """ Base form for Djinn search. This always takes the user into
    account, to be able to check on allowed content. """

    def __init__(self, *args, **kwargs):

        self.sqs = None
        self.spelling_query = None

        super(BaseSearchForm, self).__init__(*args, **kwargs)

    def search(self):

        """ Sadly we have to override the base haystack search
        completely. It just doesn't do what we want...  Add extra
        filters to the base search, so as to allow extending classes
        to do more sophisticated search. Other than the default
        implementation of haystack we don't return the searchqueryset,
        since it means that it is execeuted once more..."""

        if not self.is_valid():
            return self.no_query_found()

        if not self.has_query:
            return self.no_query_found()

        if self.cleaned_data.get('q'):
            self.sqs = self.searchqueryset.auto_query(self.cleaned_data['q'])
            self.spelling_query = AutoQuery(self.cleaned_data['q']). \
                query_string
        else:
            self.sqs = SearchQuerySet()

        if self.load_all:
            self.sqs = self.sqs.load_all()

        # Apply extra filters before doing the actual query
        self.extra_filters()

        # Apply ordering
        self.ordering()

        # Any post processing, like checking results and additional action.
        #
        self.post_run()

        self.enable_run_kwargs()

        return self.sqs

    @property
    def has_query(self):

        """ Check whether anything at all was asked """

        return filter(lambda x: x, self.cleaned_data.values())

    def run_kwargs(self):

        """ Specify a dict of keyword arguments that should be
        provided to the query run """

        return {}

    def extra_filters(self):

        """ Override this method to apply extra filters """

        pass

    def enable_run_kwargs(self):

        """ Enable override of actual run kwargs """

        _orig_build_params = self.sqs.query.build_params

        def _build_params(qry, **kwargs):

            """ Allow for extra kwargs """

            kwargs = _orig_build_params()
            kwargs.update(self.run_kwargs())

            return kwargs

        self.sqs.query.build_params = _build_params

    def post_run(self):

        """ Any manipulations to the query that need the actual
        result, e.g. count, should go here """

        pass

    def ordering(self):
        """ Apply ordering to the SearchQuerySet
        """
        pass


class SearchForm(BaseSearchForm):

    """ Default implementation. This form checks on results whether
    the current user is allowed to see it, and requeries the search
    engine in case more search terms have been provided, but no match
    was found. If the default search is 'AND', 'OR' is tried as
    well. """

    content_type = CTField(required=False)
    meta_type = CTField(required=False)

    # Tainted marker for default 'AND' that has been reinterpreted as 'OR',
    #
    and_or_tainted = False

    def __init__(self, *args, **kwargs):

        """ We always need the user... """

        self.user = kwargs['user']
        del kwargs['user']

        return super(SearchForm, self).__init__(*args, **kwargs)

    def extra_filters(self):

        self._filter_allowed()
        self._filter_ct()
        self._filter_meta_ct()

    def post_run(self):

        self._detect_and_or()
        self._add_ct_facet()

    def _detect_and_or(self):

        """ let's see whether we have something useful. If not, we'll
        try the separate query terms that are regular words and go for
        an (OR query). Unless only one term was given in the first
        place... """

        parts = split_query(self.cleaned_data['q'], self.sqs.query)

        if len(parts) > 1 and \
                getattr(settings, 'HAYSTACK_DEFAULT_OPERATOR', "AND") == "AND"\
                and not self.sqs.count():

            self.and_or_tainted = True

            self.sqs = SearchQuerySet()
            self.sqs = self.sqs.filter(content=parts[0])

            for part in parts[1:]:
                self.sqs = self.sqs.filter_or(content=part)

    def _filter_allowed(self):

        """ Do check on allowed users on all content in the set """

        access_to = ['group_users', 'user_%s' % self.user.username]

        for group in self.user.usergroup_set.all():
            access_to.append('group_%d' % group.id)

        self.sqs = self.sqs.filter(allow_list__in=access_to)

    def _filter_ct(self):

        for ct in self.cleaned_data['content_type']:

            _filter = {DJANGO_CT: ct}

            self.sqs = self.sqs.filter(**_filter)

    def _filter_meta_ct(self):

        for ct in self.cleaned_data['meta_type']:

            self.sqs = self.sqs.filter(meta_ct=ct)

    def _add_ct_facet(self):

        self.sqs = self.sqs.facet(DJANGO_CT)

    def run_kwargs(self):

        """ Provide spelling query if INCLUDE_SPELLING is set """

        if self.sqs.query.backend.include_spelling:
            return {'spelling_query': self.spelling_query}


class FixedFilterSearchForm(SearchForm):

    """ Form that enables preset filters """

    @property
    def fixed_filters(self):

        """ Implement this call to return the filters that are required """

        return []
