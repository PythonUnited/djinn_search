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

        return {"suggestion": self.results.query.get_spelling_suggestion()}

class SearchView(BaseSearchView):

    """ Basic search """
