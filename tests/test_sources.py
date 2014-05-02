from nose.tools import assert_equal, assert_false, assert_in

from tools import _check_jena, _get_test_file
from syntaxrules.syntaxtree import SyntaxTree

TEST_SAF = _get_test_file("test_saf.json")

def test_sources_nl():
    _check_jena()
    from syntaxrules.sources import get_sources_nl, get_all_sources_nl
    saf = _get_test_file("sources_nl_test.json")
    t = SyntaxTree(saf, 1)

    def normalize(sources):
        return set((tuple(sorted(s['source'])), tuple(sorted(s['quote'])))
                   for s in sources)

    expected = {((4, ), (1,3,5,6)),
                ((7, ), (2,8,9))}
    assert_equal(normalize(get_sources_nl(t)), expected)

    assert_equal(normalize(get_all_sources_nl(saf)), expected)

if __name__ == '__main__':
    test_sources_nl()
