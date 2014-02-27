"""
Pre-defined rules for detecting sources
(currently Dutch only)
"""
from os import path
import json

from syntaxrules.soh import SOHServer
from syntaxrules.syntaxtree import SyntaxTree

_CACHE = {}

def _get_ruleset(fn):
    if fn not in _CACHE:
        here = path.abspath(path.dirname(__file__))
        rules = json.load(open(path.join(here, 'rulesets', fn)))
        _CACHE[fn] = rules
    return _CACHE[fn]

def get_sources_nl(tree):
    r = _get_ruleset('sources_nl.json')
    tree.apply_ruleset(r)
    for rel in tree.get_relations():
        if rel['predicate'] == "quote":
            yield {'source' : rel['subject_nodes'],
                   "quote" : rel['object_nodes']}

def get_all_sources_nl(saf, soh_url="http://localhost:3030/x"):
    soh = SOHServer(soh_url)
    t = SyntaxTree(soh)
    for sid in {token['sentence'] for token in saf['tokens']}:
        t.load_saf(saf, sid)
        for source in get_sources_nl(t):
            yield source
