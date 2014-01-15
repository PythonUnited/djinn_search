from django import forms
from base import FixedFilterSearchForm
from django.utils.translation import ugettext_lazy as _


class UserContentSearchForm(FixedFilterSearchForm):

    owner = forms.CharField(required=True)

    spelling_query = None

    @property
    def fixed_filters(self):

        return [{'id': 'owner', 'name': str(self.user.profile)}]

    def extra_filters(self, skip_filters=None):

        self.sqs = self.sqs.filter(owner=self.cleaned_data['owner'])
