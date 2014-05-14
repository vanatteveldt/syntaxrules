from syntaxrules import SyntaxTree
import requests
import json

# create SyntaxTree object based on sentences from the unitt tests
saf_url = "https://raw.github.com/vanatteveldt/syntaxrules/master/tests/test_saf.json"
saf = open("/home/wva/syntaxrules/tests/test_saf.json")
#saf = requests.get(saf_url).json()
t = SyntaxTree(saf, sentence_id=1)

# Visualize to /tmp/test.png
#t.get_graphviz().draw("/tmp/test.png", prog="dot")

# apply rules
ruleset_url = "https://raw.github.com/vanatteveldt/syntaxrules/master/tests/test_rules.json"
#ruleset = requests.get(ruleset_url).json()
ruleset = json.load(open("/home/wva/syntaxrules/tests/test_rules.json"))
t.apply_ruleset(ruleset)
t.get_graphviz().draw("/tmp/test.png", prog="dot")
import sys; sys.exit()


# get newly created triples
triples = t.get_triples(ignore_grammatical=True)
print(triples[0].predicate)
print(triples[0].subject)

# get newly created triples in minimal json form
print t.get_triples(ignore_grammatical=True, minimal=True)

# Visualize to /tmp/test2.png, grey out syntax relations
from syntaxrules import VIS_GREY_REL
t.get_graphviz().draw("/tmp/test.png", prog="dot")
g = t.get_graphviz(triple_args_function=VIS_GREY_REL)
g.draw("/tmp/test2.png", prog="dot")
