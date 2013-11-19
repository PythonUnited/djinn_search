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

        """ Is there an implicit 'OR' performed """

        return getattr(self.form, "and_or_tainted", False)


class SearchView(BaseSearchView):

    """ Basic search """
