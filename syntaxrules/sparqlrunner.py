"""
Run a number of sparql update statements on a data source
Uses the (simple) java script SparqlRunner.java to address JENA ARQ
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
    """
    Keeps a java process with sparqlrunner in a sub process.
    Normally, use the singleton-based module-level run function rather
    than instantiating this class directly
    (unless you need e.g. multiple concurrent processes)
    """

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


_SINGLETON_LOCK = threading.Lock()
def run(data, updates, parse=True):
    """
    Run the updates on the data and return the resulting triples
    Uses a (thread-safe) singleton instance of SparqlRunner
    """
    with _SINGLETON_LOCK:
        if not hasattr(SparqlRunner, '_singleton'):
            SparqlRunner._singleton = SparqlRunner()
        return SparqlRunner._singleton.run(data, updates, parse=parse)
