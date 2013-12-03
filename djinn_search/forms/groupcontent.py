from django import forms
from base import FixedFilterSearchForm


class GroupContentSearchForm(FixedFilterSearchForm):

    group = forms.CharField(required=True)

    spelling_query = None
    fixed_filters = ["group"]

    def extra_filters(self, skip_filters=None):

        self.sqs = self.sqs.filter(parentusergroup=self.cleaned_data['group'])
