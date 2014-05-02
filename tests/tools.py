import json
import os
from os import path

from unittest import SkipTest

def _get_test_file(fn):
    here = path.abspath(path.dirname(__file__))
    return json.load(open(path.join(here, fn)))


def _check_jena():
    if 'JENA_HOME' not in os.environ:
        raise SkipTest("JENA_HOME not defined")
    if not path.exists(os.environ['JENA_HOME']):
        raise SkipTest("Could not locate JENA_HOME at {}"
                       .format(os.environ['JENA_HOME']))
