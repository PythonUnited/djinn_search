from django import forms
from base import FixedFilterSearchForm
from django.utils.translation import ugettext_lazy as _ 


class GroupContentSearchForm(FixedFilterSearchForm):

    group = forms.CharField(required=True)

    spelling_query = None

    @property
    def fixed_filters(self):

        # Translators: Display name for the fixed group filter
        return [{'id': 'group', 'value': self.cleaned_data['group'],
                 'name': _(u'Group')}]

    def extra_filters(self, skip_filters=None):

        self.sqs = self.sqs.filter(parentusergroup=self.cleaned_data['group'])
