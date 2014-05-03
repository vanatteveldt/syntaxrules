"""
Run a number of sparql update statements on a data source
Uses the simple java script SparqlRunner.java to address JENA ARQ
"""
import logging
import os, os.path
import json
import subprocess
from rdflib import Graph
import threading
import functools

def read_lines(source, target):
    """Read lines from file source and appends them to list target, until EOF or empty line"""
    while True:
        line = source.readline()
        if not (line and line.strip()):
            break
        target.append(line)

class SparqlRunner(object):

    
    def __init__(self):
        self.start_sparqlrunner()

    def start_sparqlrunner(self):
        jena = os.path.abspath(os.environ['JENA_HOME'])
        import syntaxrules
        runner = os.path.abspath(os.path.join(os.path.dirname(syntaxrules.__file__), "../sparqlrunner"))
        classpath = "{jena}/lib/*:{runner}:{runner}/javax.json-1.0.4.jar".format(**locals())
        cmd = "java -cp '{classpath}' SparqlRunner".format(**locals())
        self.p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.communicate(input=None)
        
    def communicate(self, input):
        if self.p.poll() is not None:
            logging.warn("SparqlRunner process died, respawning")
            self.start_sparqlrunner()
            
        if input:
            self.p.stdin.write(input)
            self.p.stdin.write("\n\n")
            self.p.stdin.flush()

        out_lines, err_lines = [], []
        func = functools.partial(read_lines, source=self.p.stdout, target=out_lines)
        t = threading.Thread(target=func)
        t.start()
        while True:
            line = self.p.stderr.readline().strip()
            if not line:
                raise Exception("Unexpected EOF!\n%s"%"\n".join(err_lines))
            #print "E>", line.strip()
            err_lines.append(line)
            if line == 'SparqlRunner: READY':
                break
        t.join()
        return "".join(out_lines)
        
        
    def run(self, data, updates, parse=True):
        if isinstance(data, Graph):
            data = data.serialize(format="turtle")
        input = json.dumps({"data" : data, "updates" : updates})
        out = self.communicate(input)
        if parse:
            out = Graph().parse(data=out, format='n3')
        return out

        
        
_SINGLETON = None
def _get_singleton():
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = SparqlRunner()
    return _SINGLETON

def run(data, updates, parse=True):
    """
    Run the updates on the data and return the resulting triples
    """
    return _get_singleton().run(data, updates, parse=True)

def test():
    
    r = SparqlRunner()

    data = "@prefix vCard:   <http://www.w3.org/2001/vcard-rdf/3.0#> .\n@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n\n<http://somewhere/MattJones/>  vCard:FN   \"Matt Jones\" .\n<http://somewhere/MattJones/>  vCard:N    _:b0 .\n_:b0  vCard:Family \"Jones\" .\n_:b0  vCard:Given  \"Matthew\" .\n\n\n<http://somewhere/RebeccaSmith/> vCard:FN    \"Becky Smith\" .\n<http://somewhere/RebeccaSmith/> vCard:N     _:b1 .\n_:b1 vCard:Family \"Smith\" .\n_:b1 vCard:Given  \"Rebecca\" .\n\n<http://somewhere/JohnSmith/>    vCard:FN    \"John Smith\" .\n<http://somewhere/JohnSmith/>    vCard:N     _:b2 .\n_:b2 vCard:Family \"Smith\" .\n_:b2 vCard:Given  \"John\"  .\n\n<http://somewhere/SarahJones/>   vCard:FN    \"Sarah Jones\" .\n<http://somewhere/SarahJones/>   vCard:N     _:b3 .\n_:b3 vCard:Family  \"Jones\" .\n_:b3 vCard:Given   \"Sarah\" .\n\n"
    updates = ["PREFIX vCard: <http://www.w3.org/2001/vcard-rdf/3.0#>\nINSERT { ?x vCard:FN  \"Wouter\" } WHERE {?x vCard:FN \"John Smith\"}"]

    g = r.run(data, updates)
    g = r.run(data, updates)
    print g
    updatesfout = ["PREFXIX vCard: <http://www.w3.org/2001/vcard-rdf/3.0#>\nINSERT { ?x vCard:FN  \"Wouter\" } WHERE {?x vCard:FN \"John Smith\"}"]
    try:
        g = r.run(data, updatesfout)
    except Exception, e:
        logging.exception("ERROR")
    print "----------"
    g = r.run(data, updates)


if __name__ == '__main__':
    test()
