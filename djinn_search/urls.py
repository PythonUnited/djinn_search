from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from djinn_search.views.base import SearchView
from djinn_search.forms.base import SearchForm


urlpatterns = [

    url(r'^search/', login_required(
        SearchView(load_all=False,
                   form_class=SearchForm)),
        name='djinn_search'),
]
