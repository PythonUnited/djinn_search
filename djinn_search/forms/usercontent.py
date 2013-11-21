from django import forms
from base import FixedFilterSearchForm


class UserContentSearchForm(FixedFilterSearchForm):

    owner = forms.CharField(required=True)

    def extra_filters(self):
        
        self.sqs = self.sqs.filter(owner=self.cleaned_data['owner'])
