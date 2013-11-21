from django.conf import settings
from haystack.forms import SearchForm as Base
from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet
from djinn_search.utils import split_query


class BaseSearchForm(Base):

    """ Base form for Djinn search. This always takes the user into
    account, to be able to check on allowed content. """

    # Hold searchqueryset in local variable, to prevent early evaluation
    #
    sqs = None
    
    def search(self):

        """ Add extra filters to the base search, so as to allow
        extending classes to do more sophisticated search. Other than
        the default implementation of haystack we don't return the
        searchqueryset, since it means that it is execeuted once
        more... """

        self.sqs = super(BaseSearchForm, self).search()

        # Apply extra filters before doing the actual query
        self.extra_filters()

        self.enable_run_kwargs()
        
        # Any post processing, like checking results and additional action.
        #
        self.post_run()

        return self.sqs

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

            kwargs = _orig_build_params()
            kwargs.update(self.run_kwargs())
            
            return kwargs

        self.sqs.query.build_params = _build_params

    def post_run(self):

        """ Any manipulations to the query that need the actual
        result, e.g. count, should go here """

        pass


class SearchForm(BaseSearchForm):

    """ Default implementation. This form checks on results whether
    the current user is allowed to see it, and requeries the search
    engine in case more search terms have been provided, but no match
    was found. If the default search is 'AND', 'OR' is tried as
    well. """

    # Tainted marker for default 'AND' that has been reinterpreted as 'OR',
    #
    and_or_tainted = False

    def __init__(self, *args, **kwargs):

        """ We always need the user... """

        self.user = kwargs['user']
        del kwargs['user']

        return super(BaseSearchForm, self).__init__(*args, **kwargs)

    def extra_filters(self):

        self._filter_allowed()

    def post_run(self):

        self._detect_and_or()
        
    def _detect_and_or(self):
        
        """ let's see whether we have something useful. If not, we'll
        try the separate query terms that are regular words and go for
        an (OR query). Unless only one term was given in the first
        place... """
        
        parts = split_query(self.cleaned_data['q'], self.sqs.query)

        if len(parts) > 1 and \
                getattr(settings, 'HAYSTACK_DEFAULT_OPERATOR', "AND") == "AND" \
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

    def run_kwargs(self):

        """ Provide spelling query if INCLUDE_SPELLING is set """

        if self.sqs.query.backend.include_spelling:
            return {'spelling_query':
                        AutoQuery(self.cleaned_data['q']).query_string}
