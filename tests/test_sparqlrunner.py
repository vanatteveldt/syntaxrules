from nose.tools import assert_equal, assert_false, assert_in, assert_not_in

from rdflib import Graph

from syntaxrules.sparqlrunner import SparqlRunner

def test_sparql():
    from tools import _check_jena
    _check_jena()
    r = SparqlRunner()

    data = """
    @prefix vCard:   <http://www.w3.org/2001/vcard-rdf/3.0#> .
    @prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    <http://somewhere/MattJones/>  vCard:FN   "Matt Jones" .
    <http://somewhere/MattJones/>  vCard:N    _:b0 .
    _:b0  vCard:Family "Jones" .
    _:b0  vCard:Given  "Matthew" .
    """
    update = '''PREFIX vCard: <http://www.w3.org/2001/vcard-rdf/3.0#>
                DELETE {?x vCard:FN "Matt Jones"}
                INSERT {?x vCard:FN  "Matty" }
                WHERE {?x vCard:FN "Matt Jones"}'''

    g = r.run(data, [update])
    rels = {tuple(map(str, spo)) for spo in list(g)}
    MATT, FN = 'http://somewhere/MattJones/', 'http://www.w3.org/2001/vcard-rdf/3.0#FN'
    # insert worked?
    assert_in((MATT, FN, 'Matty'), rels)
    # delete worked?
    assert_not_in((MATT, FN, 'Matt Jones'), rels)

    # test rdflib Graph input
    Graph().parse(data=data, format='n3')
    g = r.run(data, [update])
    assert_in((MATT, FN, 'Matty'), rels)

    # test error handling, is the sparql exception reproduced
    try:
        r.run(data, ["THIS IS NOT VALID SPARQL"])
    except Exception, e:
        assert_in("Lexical error", str(e))
    else:
        assert False
