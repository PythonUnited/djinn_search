from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from base import FixedFilterSearchForm


class UserContentSearchForm(FixedFilterSearchForm):

    owner = forms.CharField(required=True)

    spelling_query = None

    @property
    def fixed_filters(self):

        return [{'id': 'owner', 'name': str(self.user.profile)}]

    def extra_filters(self, skip_filters=None):

        self.sqs = self.sqs.filter(owner=self.cleaned_data['owner'])

        # Although the owner own's his/her profile, this is not
        # regarded 'content'
        #
        self.sqs = self.sqs.exclude(
            meta_ct=(settings.DJINN_USERPROFILE_MODEL or
                     "djinn_profiles.userprofile"))
