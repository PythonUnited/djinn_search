import logging
from django.forms import CharField
from djinn_contenttypes.registry import CTRegistry
from djinn_search.widgets.contenttype import CTWidget


LOGGER = logging.getLogger('djinn_search')


class CTField(CharField):

    """ Content type field that can hold multiple values """

    widget = CTWidget

    def clean(self, value):

        normalized = []

        for ct in value:

            if len(ct.split(".")) == 2:
                normalized.append(ct)
            elif len(ct.split(".")) == 1:
                ct_info = CTRegistry.get(ct)
                try:
                    normalized.append("%s.%s" % (ct_info['app'], ct))
                except:
                    # igore odd ctypes
                    pass

        return normalized
