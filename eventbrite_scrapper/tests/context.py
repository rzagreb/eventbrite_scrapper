import os
import sys

DPATH_APP = os.path.dirname((os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath(DPATH_APP))

import eventbrite_scrapper  # noqa: E402, F401
