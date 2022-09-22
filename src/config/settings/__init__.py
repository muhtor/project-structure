from os import environ
# import os
# MODE = os.environ.get("DEBUG")
# if MODE:
#     from .development import *x
# else:
#     from .production import *

if environ['DJANGO_SETTINGS_MODULE'] == 'goserver.settings':
    # from .development import *
    from .production import *

