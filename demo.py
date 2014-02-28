"""
Demo of applying a ruleset to a sentence parsed using Alpino

Requires:
- xtas and syntaxrules on the PYTHONPATH
- ALPINO_HOME pointing to binary install of Alpino
- Sparql server reachable on http://localhost:3030/x

See: http://github.com/vanatteveldt/xtas
     http://github.com/vanatteveldt/syntaxrules

(If you don't have xtas+Alpino, you can also just load a saf file from disk)
"""

import sys
import json
from os import path

from xtas.tasks.pipeline import pipeline
from xtas.tasks import app

import syntaxrules
from syntaxrules.sources import get_all_sources_nl

s = "Dit gaat makkelijk volgens Wouter"

# (1) Parse the sentence
# we don't want to use the multiprocessing
app.conf['CELERY_ALWAYS_EAGER'] = True
saf = pipeline(s, [{"module": "xtas.tasks.single.alpino"}])

# (2) Run ruleset

# Option 1: shortcut with existing rules in sources_nl
saf['quotes'] = list(get_all_sources_nl(saf))

# Output: Print quotes as string
print "\nQuotes according to get_all_sources_nl:"
lemmata = {t['id'] : t['lemma'] for t in saf['tokens']}
for quote in saf['quotes']:
    source = ",".join(lemmata[s] for s in quote['source'])
    quote = ",".join(lemmata[s] for s in quote['quote'])
    print source, ":", quote

# Output: Write 'enriched' SAF to file
json.dump(saf, open("/tmp/sentence.json", "w"), indent=2)
print "\nSaf written to /tmp/sentence.json"

# Option 2: 'manual' setup with rules file
#  a Load saf into 'SyntaxTree'
soh = syntaxrules.SOHServer(url="http://localhost:3030/x")
t = syntaxrules.SyntaxTree(soh)
t.load_saf(saf, sentence_id=1)

# Load and apply ruleset
filename = path.join(path.dirname(syntaxrules.__file__), "rulesets", "sources_nl.json")
ruleset = json.load(open(filename))
t.apply_ruleset(ruleset)

# Output: print
print "\nRelations after applying ruleset:"
for rel in t.get_relations():
    print rel

# Output: Visualize as network diagram
# (VIS_GREY_REL makes the syntactic relations grey)
g = t.get_graphviz(triple_args_function=syntaxrules.VIS_GREY_REL)
g.draw("/tmp/quote.png", prog="dot")
print "\nNetwork diagram written to /tmp/quote.png"
