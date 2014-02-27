import json
from os import path

from unittest import SkipTest
from syntaxrules.soh import SOHServer
from syntaxrules.syntaxtree import SyntaxTree



def _get_test_file(fn):
    here = path.abspath(path.dirname(__file__))
    return json.load(open(path.join(here, fn)))


def _check_soh():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = s.connect(('127.0.0.1', 3030))
    except:
        logging.exception("Could not connect to SOH server")
        raise SkipTest("Could not connect to SOH Server at 127.0.0.1:3300, "
                       "skipping test")


def _get_tree(saf, sid=1):
    _check_soh()
    soh = SOHServer(url="http://localhost:3030/x")
    t = SyntaxTree(soh)
    t.load_saf(saf, sid)
    return t
