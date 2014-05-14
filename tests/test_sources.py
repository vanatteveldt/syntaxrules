from nose.tools import assert_equal, assert_false, assert_in

from tests.tools import _check_jena, _get_test_file
from syntaxrules.sources import get_sources_nl, get_sources_en


def test_sources_nl():
    _check_jena()
    saf = _get_test_file("sources_nl_test.json")

    def normalize(sources):
        sources = ({role: sorted(int(n.id) for n in nodes) for (role, nodes) in source.iteritems()}
                   for source in sources)
        return sorted(sources, key = lambda struct: struct['predicate'])

    expected = [{'predicate' : [4], 'quote': [1, 3, 5, 6]},
                {'predicate' : [7], 'quote': [2, 8, 9]}]

    assert_equal(normalize(get_sources_nl(saf)), expected)


def test_sources_en():
    _check_jena()
    saf = _get_test_file("sources_en_test.json")

    def normalize(sources):
        sources = ({role: sorted(int(n.id) for n in nodes) for (role, nodes) in source.iteritems()}
                   for source in sources)
        return sorted(sources, key = lambda struct: struct['predicate'])

    expected = [{'predicate' : [2], 'source': [1], 'quote': [3, 4, 5, 6]}]

    assert_equal(normalize(get_sources_en(saf)), expected)

if __name__ == '__main__':
    test_sources_nl()
