import tempfile

from nose.tools import assert_equal, assert_false, assert_in

from syntaxrules.syntaxtree import SyntaxTree, NS_AMCAT
#from syntaxrules.syntaxtree import VIS_GREY_REL,
from tools import _check_jena, _get_test_file

TEST_SAF = _get_test_file("test_saf.json")
TEST_RULES = _get_test_file("test_rules.json")


def test_saf_to_rdf():
    from syntaxrules.syntaxtree import _saf_to_rdf

    triples = set(tuple(str(x).replace("http://amcat.vu.nl/amcat3/", ":")
                        for x in spo)
                  for spo in _saf_to_rdf(TEST_SAF, sentence_id=1))

    from_john = set((p, o) for (s, p, o) in triples
                    if s == ':t_1_John')
    assert_equal(from_john, {(':sentence', '1'),
                             (':word', 'John'),
                             (':offset', '1'),
                             (':pos', 'NNP'),
                             (':id', '1'),
                             (':lemma', 'John'),
                             (':rel_nsubj', ':t_2_marry'),
                             (':rel', ':t_2_marry'),
                             })

    subjects = set(s for (s, p, o) in triples)
    assert_equal(subjects, {':t_1_John', ':t_2_marry', ':t_3_Mary',
                            ':t_4_little'})

    triples = set(tuple(str(x).replace("http://amcat.vu.nl/amcat3/", ":")
                        for x in spo)
                  for spo in _saf_to_rdf(TEST_SAF, sentence_id=2))

    subjects = set(s for (s, p, o) in triples)
    assert_equal(subjects, {':t_5_it', ':t_6_rain'})
    relations = set((s, p, o) for (s, p, o) in triples if o.startswith(":"))
    assert_equal(relations, {(':t_5_it', ':rel', ':t_6_rain'),
                             (':t_5_it', ':rel_nsubj', ':t_6_rain')})


def test_load():
    _check_jena()
    t = SyntaxTree(TEST_SAF, sentence_id=2)
    triples = list(t.get_triples())
    assert_equal(len(triples), 1)
    assert_equal(triples[0].predicate, 'rel_nsubj')
    assert_equal(triples[0].subject.lemma, 'it')
    assert_equal(triples[0].object.lemma, 'rain')


def test_lexicon():
    _check_jena()
    t = SyntaxTree(TEST_SAF, sentence_id=1)
    t.apply_lexicon(TEST_RULES['lexicon'])

    classes = {k.replace(NS_AMCAT, ":"): v.get('lexclass')
               for (k, v) in t.get_tokens().iteritems()}
    assert_equal(classes, {":t_2_marry": ["marry"],
                           ":t_3_Mary": ['person'],
                           ':t_1_John': ['person'],
                           ':t_4_little': None,
                       })


def test_rules():
    _check_jena()
    t = SyntaxTree(TEST_SAF, sentence_id=1)
    t.apply_ruleset(TEST_RULES)
    triples = [tr for tr in t.get_triples() if tr.predicate == "marry"]

    assert_equal(len(triples), 1)
    assert_equal(triples[0].subject.lemma, 'John')
    assert_equal(triples[0].object.lemma, 'Mary')


def test_graph():
    _check_jena()
    t = SyntaxTree(TEST_SAF, sentence_id=1)
    g = t.get_graphviz()
    assert_equal(set(g.edges()), {(u't_3_Mary', u't_2_marry'),
                                  (u't_1_John', u't_2_marry'),
                                  (u't_4_little', u't_1_John'),
                              })
    assert_in("lemma: John", g.get_node("t_1_John").attr["label"])

    # Can we 'gray out' syntax relations after applying rules
    t.apply_ruleset(TEST_RULES)
    t.apply_lexicon([{"lexclass": "man", "lemma": "john"}])
    g = t.get_graphviz()#triple_args_function=VIS_GREY_REL)
    assert_equal(set(g.edges()), {(u't_3_Mary', u't_2_marry'),
                                  (u't_1_John', u't_2_marry'),
                                  (u't_4_little', u't_1_John'),
                                  (u't_1_John', u't_3_Mary')})
    #assert_false(g.get_edge(u't_1_John', u't_3_Mary').attr.get("color"))
    #assert_equal(g.get_edge(u't_1_John', u't_2_marry').attr.get("color"),
    #"grey")

    # can we draw it? can't check output, but we can check for errors
    with tempfile.NamedTemporaryFile() as f:
        g.draw(f.name, prog="dot")
        g.draw("/tmp/test.png", prog="dot")

def test_get_triples():
    _check_jena()
    t = SyntaxTree(TEST_SAF, sentence_id=1)
    t.apply_ruleset(TEST_RULES)
    rels = list(t.get_relations())
    marry = dict(predicate='marry', object=3, object_nodes=[3],
                 subject=1, subject_nodes=[1,4])
    assert_equal(rels, [marry])

    # add new relation, see if percolation is 'blocked' by relation
    t.apply_rule({"condition" : "?x :rel_dobj ?y",
                  "insert" : "?y :test ?x"})
    rels = sorted(t.get_relations(), key=lambda rel: rel['predicate'])
    assert_equal(rels[0], marry)
    assert_equal(rels[1], dict(predicate='test',
                               object=3, object_nodes=[3],
                               subject=2, subject_nodes=[2]))

if __name__ == '__main__':
    test_get_triples()
