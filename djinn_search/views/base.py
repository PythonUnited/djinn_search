from haystack.views import SearchView as Base


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

        return {"suggestion": self.results.query.get_spelling_suggestion(),
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
