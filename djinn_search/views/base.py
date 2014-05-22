from haystack.views import SearchView as Base
from django.views.generic.detail import SingleObjectMixin


class BaseSearchView(Base):

    template = "djinn_search/search.html"

    def build_form(self, form_kwargs=None):

        """ Override base build_form so as to add the user to the context """

        if not form_kwargs:
            form_kwargs = {}

        form_kwargs['user'] = self.request.user

        return super(BaseSearchView, self).build_form(form_kwargs=form_kwargs)

    def is_tainted_and_or(self):

        """ Is an implicit 'OR' performed? This may be the case if no
        results were found with a query that contained multiple
        terms. """

        return getattr(self.form, "and_or_tainted", False)

    def extra_context(self):

        suggestion = ""

        if self.form.spelling_query:
            try:
                suggestion = self.results.query.get_spelling_suggestion()

                if not hasattr(suggestion, "encode"):
                    suggestion = ""
            except:
                pass

        return {"suggestion": suggestion,
                "is_tainted_and_or": self.is_tainted_and_or}


class SearchView(BaseSearchView):

    """ Basic search """

    def create_response(self):

        """
        Generates the actual HttpResponse to send back to the
        user. This may be an ajax call, in which case we set the
        content type to plain.
        """

        res = super(SearchView, self).create_response()

        if self.request.is_ajax():
            res._headers['content-type'] = \
                ('Content-Type', 'text/plain; charset=utf-8')

        return res


class CTSearchView(SearchView, SingleObjectMixin):

    model = None

    def __init__(self, *args, **kwargs):

        self.model = kwargs.pop('model', None)
        self.kwargs = kwargs

        super(CTSearchView, self).__init__(*args, **kwargs)

    def extra_context(self):

        ctx = super(CTSearchView, self).extra_context()

        ctx.update(self.get_context_data())

        ctx['object'] = self.object

        return ctx

    def __call__(self, request):

        self.request = request
        self.object = self.get_object()

        return super(CTSearchView, self).__call__(request)
