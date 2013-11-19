from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from pgsearch.views.base import SearchView
from pgsearch.forms.base import SearchForm


urlpatterns = patterns("pgsearch.views",

    url(r'^search/', login_required(
            SearchView(load_all=False,
                       form_class=SearchForm)),
        name='djinn_search'),
)
