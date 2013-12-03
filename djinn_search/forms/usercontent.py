from django import forms
from base import FixedFilterSearchForm


class UserContentSearchForm(FixedFilterSearchForm):

    owner = forms.CharField(required=True)

    spelling_query = None
    fixed_filters = ["owner"]

    def extra_filters(self, skip_filters=None):

        self.sqs = self.sqs.filter(owner=self.cleaned_data['owner'])
