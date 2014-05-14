"""
Pre-defined rules for detecting sources
(currently Dutch only)
"""
from os import path
import json

from syntaxrules.syntaxtree import SyntaxTree

_CACHE = {}

def _get_ruleset(fn):
    if fn not in _CACHE:
        here = path.abspath(path.dirname(__file__))
        rules = json.load(open(path.join(here, 'rulesets', fn)))
        _CACHE[fn] = rules
    return _CACHE[fn]


def get_sources(saf, ruleset_name):
    r = _get_ruleset(ruleset_name)
    tree = SyntaxTree(saf)
    tree.apply_ruleset(r)
    return [struct for struct in tree.get_structs() if 'quote' in struct.keys()]


def get_sources_nl(saf):
    return get_sources(saf, 'sources_nl.json')

def get_sources_en(saf):
    return get_sources(saf, 'sources_en.json')
