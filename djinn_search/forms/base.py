from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from haystack.forms import SearchForm as Base
from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet
from haystack.constants import DJANGO_CT
from haystack.backends import SQ
from djinn_search.utils import split_query
from djinn_search.fields.contenttype import CTField


ORDER_BY_OPTIONS = (('', _('Relevance')),
                    ('-changed', _('Last modified')),
                    ('-published', _('Published')),
                    ('title_exact', _('Alphabetical')))


class BaseSearchForm(Base):

    """ Base form for Djinn search. This always takes the user into
    account, to be able to check on allowed content. """
    keywords = forms.CharField(required=False, label=_('Keywords'),
                        widget=forms.TextInput(attrs={'type': 'search'}))

    def __init__(self, *args, **kwargs):

        self.sqs = None
        self.spelling_query = None

        super(BaseSearchForm, self).__init__(*args, **kwargs)

    def search(self, skip_filters=None):

        """ Sadly we have to override the base haystack search
        completely. It just doesn't do what we want...  Add extra
        filters to the base search, so as to allow extending classes
        to do more sophisticated search. Other than the default
        implementation of haystack we don't return the searchqueryset,
        since it means that it is executed once more...

        If skip_filters is provided, forget about the call to
        extra_filters...
        """

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
        self.extra_filters(skip_filters=skip_filters)

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

    def extra_filters(self, skip_filters=None):

        """ Override this method to apply extra filters. If skip_filters
        is a list, any filters in this list will be skipped """

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


class SearchForm(BaseSearchForm):

    """ Default implementation. This form checks on results whether
    the current user is allowed to see it, and requeries the search
    engine in case more search terms have been provided, but no match
    was found. If the default search is 'AND', 'OR' is tried as
    well. """

    content_type = CTField(required=False)
    meta_type = CTField(required=False)
    order_by = forms.CharField(required=False,
                               # Translators: djinn_search order_by label
                               label=_('Order by'),
                               widget=forms.Select(choices=ORDER_BY_OPTIONS)
                               )

    # Tainted marker for default 'AND' that has been reinterpreted as 'OR',
    #
    and_or_tainted = False

    def __init__(self, *args, **kwargs):

        """ We always need the user... """

        self.user = kwargs['user']
        del kwargs['user']

        return super(SearchForm, self).__init__(*args, **kwargs)

    def clean_q(self):

        data = self.cleaned_data

        return data['q'].replace("'", "*")

    def extra_filters(self, skip_filters=None):

        if not skip_filters:
            skip_filters = []

        if "allowed" not in skip_filters:
            self._filter_allowed()

        if "ct" not in skip_filters:
            self._filter_ct()

        if "meta_ct" not in skip_filters:
            self._filter_meta_ct()

        if self.cleaned_data.get('keywords', None):
            self.sqs = self.sqs.filter(
                keywords__exact=self.cleaned_data.get('keywords', None))

    def post_run(self):

        self._detect_and_or()
        self._add_ct_facet()
        self._add_meta_ct_facet()
        self._order()

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

            content_filter = SQ(content=AutoQuery(parts[0]))

            for part in parts[1:]:
                content_filter = content_filter | SQ(content=AutoQuery(part))

            self.sqs.query.query_filter.children[0] = content_filter

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

    def _add_meta_ct_facet(self):

        self.sqs = self.sqs.facet("meta_ct")

    def _order(self):

        """ Apply order is found in the order_by parameter """

        if self.cleaned_data.get("order_by"):
            self.sqs = self.sqs.order_by(self.cleaned_data["order_by"])

    def run_kwargs(self):

        """ Provide spelling query if INCLUDE_SPELLING is set """

        kwargs = {}

        if self.sqs.query.backend.include_spelling and \
                self.cleaned_data.get('q'):
            kwargs['spelling_query'] = self.spelling_query

        return kwargs


class FixedFilterSearchForm(SearchForm):

    """ Form that enables preset filters """

    @property
    def fixed_filters(self):

        """
        Implement this call to return the filters that are required
        each element should be a map with an id (the value) and a name
        {'id': 'owner', 'name': 'Jan Barkhof'}
        TODO: this currently is used as a view feature, but should really
        be used only in actual filtering.
        """

        return []
