"""
Run a number of sparql update statements on a data source
Uses the simple java script SparqlRunner.java to address JENA ARQ
"""

import os, os.path
import json
import subprocess
from rdflib import Graph

def run(data, updates, parse=True):
    """
    Run the updates on the data and return the resulting triples
    """

    if isinstance(data, Graph):
        data = data.serialize(format="turtle")

    jena = os.path.abspath(os.environ['JENA_HOME'])
    import syntaxrules
    runner = os.path.abspath(os.path.join(os.path.dirname(syntaxrules.__file__), "../sparqlrunner"))
    classpath = "{jena}/lib/*:{runner}:{runner}/javax.json-1.0.4.jar".format(**locals())
    cmd = "java -cp '{classpath}' SparqlRunner".format(**locals())
    input = json.dumps({"data" : data, "updates" : updates})

    p =subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate(input)

    if 'SparqlRunner: DONE' not in err:
        raise Exception("Problem in running updates:\n{err}".format(**locals()))
    if parse:
        out = Graph().parse(data=out, format='n3')
    return out



if __name__ == '__main__':
    data = "@prefix vCard:   <http://www.w3.org/2001/vcard-rdf/3.0#> .\n@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n\n<http://somewhere/MattJones/>  vCard:FN   \"Matt Jones\" .\n<http://somewhere/MattJones/>  vCard:N    _:b0 .\n_:b0  vCard:Family \"Jones\" .\n_:b0  vCard:Given  \"Matthew\" .\n\n\n<http://somewhere/RebeccaSmith/> vCard:FN    \"Becky Smith\" .\n<http://somewhere/RebeccaSmith/> vCard:N     _:b1 .\n_:b1 vCard:Family \"Smith\" .\n_:b1 vCard:Given  \"Rebecca\" .\n\n<http://somewhere/JohnSmith/>    vCard:FN    \"John Smith\" .\n<http://somewhere/JohnSmith/>    vCard:N     _:b2 .\n_:b2 vCard:Family \"Smith\" .\n_:b2 vCard:Given  \"John\"  .\n\n<http://somewhere/SarahJones/>   vCard:FN    \"Sarah Jones\" .\n<http://somewhere/SarahJones/>   vCard:N     _:b3 .\n_:b3 vCard:Family  \"Jones\" .\n_:b3 vCard:Given   \"Sarah\" .\n\n"
    updates = ["PREFIX vCard: <http://www.w3.org/2001/vcard-rdf/3.0#>\nINSERT { ?x vCard:FN  \"Wouter\" } WHERE {?x vCard:FN \"John Smith\"}"]

    run(data, updates)
