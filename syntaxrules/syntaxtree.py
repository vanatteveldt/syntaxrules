###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

"""
Syntax tree represented in RDF
"""
import re
from collections import namedtuple, defaultdict
from itertools import chain
import logging
import json

import requests
from unidecode import unidecode
from rdflib import ConjunctiveGraph, Namespace, Literal
from pygraphviz import AGraph

import sparqlrunner

from .soh import SOHServer

log = logging.getLogger(__name__)

AMCAT = "http://amcat.vu.nl/amcat3/"
NS_AMCAT = Namespace(AMCAT)
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
Triple = namedtuple("Triple", ["subject", "predicate", "object"])

VIS_IGNORE_PROPERTIES = "id", "offset", "sentence", "uri", "word"
VIS_THEME_OPTIONS = {"graph" : {"rankdir" : "BT",
                                "concentrate" : "false"},
                     "node" : {"shape" : "rect",
                               "fontsize" : 10},
                     "edge" : {"edgesize" : 10,
                               "fontsize" : 10}}

class Node(object):
    """
    Flexible 'record-like' object with arbitrary attributes for tokens
    """
    def __unicode__(self):
        return "Node(%s)" % ", ".join("%s=%r" % kv
                                      for kv in self.__dict__.iteritems())

    def __init__(self, **kargs):
        self.__dict__.update(kargs)
    __repr__ = __unicode__


def graphviz_node_hook(node, **_):
    label = node.word if hasattr(node, "word") else node.label
    labels = ["%s: %s" % (node.id, label)]
    labels += ["%s: %s" % (k, v)
               for k, v in node.__dict__.iteritems()
               if k not in VIS_IGNORE_PROPERTIES]
    return {"label": "\\n".join(labels)}

def graphviz_triple_hook(triple, grey_rel=False, **_):
    kargs = {}
    if grey_rel and 'rel_' in triple.predicate:
        kargs['color'] = 'grey'
    if triple.predicate.startswith('frame_'):
        kargs['weight'] = 0
        # color depending on frame
        import hashlib
        hash = hashlib.sha1(triple.predicate.split("_")[1]).hexdigest()
        kargs['color'] = "#" + hash[:6]
    if 'label' not in kargs:
        kargs['label'] = triple.predicate
    return kargs

class SyntaxTree(object):

    def __init__(self, saf_article, sentence_id):
        """
        Construct a SyntaxTree object from a SAF article
        (see https://gist.github.com/vanatteveldt/9027118)
        @param saf_article: a dict, url, or file
        """
        if isinstance(saf_article, file):
            saf_article = json.load(saf_article)
        elif isinstance(saf_article, (str, unicode)):
            saf_article = requests.get(saf_article).json()
        self.saf_article = saf_article
        self.graph = ConjunctiveGraph()
        self.graph.bind("amcat", AMCAT)
        for triple in _saf_to_rdf(saf_article, sentence_id):
            self.graph.add(triple)


    def get_triples(self, ignore_rel=True, filter_predicate=None,
                    ignore_grammatical=False, minimal=False):
        """Retrieve the triples for the loaded sentence"""
        result = []
        if isinstance(filter_predicate, (str, unicode)):
            filter_predicate = [filter_predicate]
        nodes = {}
        for s, p, o in self.graph:
            s = unicode(s)
            child = nodes.setdefault(s, Node(uri=s))

            pred = str(p).replace(AMCAT, "")
            if isinstance(o, Literal):
                if hasattr(child, pred):
                    o = getattr(child, pred) + "; " + o
                setattr(child, pred, unicode(o))
            else:
                o = unicode(o)
                if not ((ignore_rel and pred == "rel")
                        or (ignore_grammatical and pred.startswith("rel_"))
                        or (filter_predicate and pred not in filter_predicate)
                        or (pred == RDF_TYPE)):
                    parent = nodes.setdefault(o, Node(uri=o))
                    result.append(Triple(child, pred, parent))

        if minimal:
            return [{"subject": s.id,"predicate": p, "object": o.id}
                    for (s, p, o) in result]
        return result

    def apply_updates(self, updates):
        def update_sparql(condition="", insert="", remove="", **_):
            return u"""PREFIX : <{AMCAT}>
                       DELETE {{ {remove} }}
                       INSERT {{ {insert} }}
                       WHERE {{ {condition} }}""".format(AMCAT=AMCAT, **locals())
        updates = [update_sparql(**u) for u in updates]
        self.graph = sparqlrunner.run(self.graph, updates)

    def apply_ruleset(self, ruleset):
        """
        Apply a set of rules to this tree.
        A ruleset should be a dict with rules and lexicon entries
        """
        updates = [self._get_lexicon_update(ruleset['lexicon'])]
        updates += ruleset['rules']
        self.apply_updates(updates)

    def apply_rule(self, rule):
        self.apply_updates([rule])
    def apply_lexicon(self, lexicon):
        updates = [self._get_lexicon_update(lexicon)]
        self.apply_updates(updates)

    def _get_lexicon_update(self, lexicon):
        """
        Lexicon should consist of dicts with lexclass, lemma, and optional pos
        lemma can be a list or a string
        """

        def merge(lists):
            """
            Merge the lists so lists with overlap are joined together
            (i.e. [[1,2], [3,4], [2,5]] --> [[1,2,5], [3,4]])
            from: http://stackoverflow.com/a/9400562
            """
            newsets, sets = [set(lst) for lst in lists if lst], []
            while len(sets) != len(newsets):
                sets, newsets = newsets, []
                for aset in sets:
                    for eachset in newsets:
                        if not aset.isdisjoint(eachset):
                            eachset.update(aset)
                            break
                    else:
                        newsets.append(aset)
            return newsets

        def get_coreferences(coreferences):
            """Decode the SAF coreferences as (node: coreferencing_nodes) pairs"""
            coref_groups = []
            for a, b in coreferences:
                # take only the heads of each coref group
                coref_groups.append([a[0], b[0]])
            for nodes in merge(coref_groups):
                for node in nodes:
                    yield node, nodes

        coreferences = dict(get_coreferences(self.saf_article.get('coreferences', [])))

        classes = defaultdict(set) #  token -> classes
        uris = {}
        for uri, token in self.get_tokens().iteritems():
            if 'pos' not in token: continue # not a word
            uris[int(token['id'])] = uri
            pos = token['pos']
            lemma = token['lemma'].lower()
            for lex in lexicon:
                if "pos" in lex and lex['pos'] != pos:
                    continue
                lemmata = lex['lemma']
                lexclass = lex['lexclass']
                if not isinstance(lemmata, list):
                    lemmata = [lemmata]
                for target in lemmata:
                    if target == lemma or (target.endswith("*")
                                           and lemma.startswith(target[:-1])):
                        id = int(token['id'])
                        for id in coreferences.get(id, [id]):
                            classes[id].add(lexclass)
        inserts = []
        for id, lexclasses in classes.iteritems():
            if id not in uris:
                continue #  coref to different sentence
            uri = str(uris[id]).replace(AMCAT, ":")
            for lexclass in lexclasses:
                inserts.append('{uri} :lexclass "{lexclass}"'.format(**locals()))
        return {"insert": ".\n".join(inserts)}


    def get_tokens(self):
        tokens = defaultdict(dict)  # id : {attrs}
        for s, p, o in self.graph:
            if isinstance(o, Literal):
                attr = p.replace(NS_AMCAT, "")
                if attr == "lexclass":
                    tokens[s][attr] = tokens[s].get(attr, []) + [unicode(o)]
                else:
                    tokens[s][attr] = unicode(o)
        return tokens


    def get_descendants(self, node, triples):
        """
        Get all decendants of node according to rel_ triples,
        but blocks on any node in a non-rel_ triple
        """
        children = defaultdict(list)  # parent id : [child ids]
        inrelation = set()  # ids of all nodes in a relation
        for s, p, o in triples:
            s, o = int(s.id), int(o.id)
            if p.startswith("rel_"):
                children[o].append(s)
            else:
                inrelation |= {s, o}
        seen = set()
        def getnodes(n):
            if n in seen:
                return
            seen.add(n)
            yield n
            for c in children[n]:
                if c not in inrelation:
                    for n2 in getnodes(c):
                        yield n2
        return getnodes(node)

    def get_relations(self):
        """
        Return all non-syntactic (ie non-rel_*) triples
        subject and object are given as head and as a list of nodes
        where the list consists of all lower nodes not in another function
        """
        triples = list(self.get_triples())

        for s, p, o in triples:
            if not p.startswith("rel"):
                s, o = int(s.id), int(o.id)
                yield {"predicate": p,
                       "subject": s,
                       "subject_nodes": list(self.get_descendants(s, triples)),
                       "object": o,
                       "object_nodes": list(self.get_descendants(o, triples)),
                   }

    def get_graphviz(self, triple_hook=graphviz_triple_hook,
                     node_hook=graphviz_node_hook,
                     theme_options=VIS_THEME_OPTIONS, **hook_options):
        """
        Create a pygraphviz graph from the tree
        @param triple_hook: a function that returns an attribute dict (or None)
                            given a triple and the kargs
        @param node_hook: a function that returns a label given a node
                           and the kargs
        @param theme_options: a dict-of-dicts containing global
                              graph/node/edge attributes
        @param hook_options: additional arguments to pass to the hook functions
        """
        def _id(node):
            return node.uri.split("/")[-1]
        g = AGraph(directed=True, strict=False)
        triples = list(self.get_triples())
        # create nodes
        nodeset = set(chain.from_iterable((t.subject, t.object)
                                          for t in triples))
        for n in sorted(nodeset, key=lambda n:n.id):
            g.add_node(_id(n), **node_hook(n, **hook_options))
        connected = set()
        # create edges
        for triple in sorted(triples, key=lambda t:t.predicate):
            kargs = triple_hook(triple, **hook_options)
            if kargs:
                if kargs.get('reverse'):
                    g.add_edge(_id(triple.object), _id(triple.subject), **kargs)
                else:
                    g.add_edge(_id(triple.subject), _id(triple.object), **kargs)
                connected |= {_id(triple.subject), _id(triple.object)}
        connected = chain.from_iterable(g.edges())
        for isolate in set(g.nodes()) - set(connected):
            g.remove_node(isolate)
        # some theme options
        for obj, attrs in theme_options.iteritems():
            for k, v in attrs.iteritems():
                getattr(g, "%s_attr" % obj)[k] = v
        return g


def _saf_to_rdf(saf_article, sentence_id):
    """
    Get the raw RDF subject, predicate, object triples
    representing the given analysed sentence
    """
    def _token_uri(token):
        lemma = re.sub("\W","",unidecode(unicode(token['lemma'])))
        uri = "t_{id}_{lemma}".format(id=token['id'], lemma=lemma)
        return NS_AMCAT[uri]

    def _rel_uri(dependency):
        rel = dependency['relation']
        rel = re.sub("[^\w-]", "", rel)
        return NS_AMCAT["rel_{rel}".format(**locals())]

    tokens = {}  # token_id : uri
    for token in saf_article['tokens']:
        if int(token['sentence']) == sentence_id:
            uri = _token_uri(token)
            for k, v in token.iteritems():
                yield uri, NS_AMCAT[k], Literal(unidecode(unicode(v)))
            tokens[int(token['id'])] = uri

    parents = {}  # child_id : parent_id, store to filter frames
    for dep in saf_article['dependencies']:
        if int(dep['child']) in tokens:
            child = tokens[int(dep['child'])]
            parent = tokens[int(dep['parent'])]
            for pred in _rel_uri(dep), NS_AMCAT["rel"]:
                yield child, pred, parent
                parents[int(dep['child'])] = int(dep['parent'])

    def is_child(child, parent):
        if child == parent: return True
        if child not in parents: return False
        return is_child(parents[child], parent)

    def has_ancestor(node, other_nodes):
        for o in other_nodes:
            if is_child(node, o):
                return True

    if 'frames' in saf_article:
        for i, f in enumerate(f for f in saf_article['frames']
                              if int(f['sentence']) == sentence_id):
            for target in f["target"]:
                yield tokens[target], NS_AMCAT["frame"], Literal(f["name"])
                for e in f["elements"]:
                    rel_uri = NS_AMCAT["frame_{ename}"
                                       .format(i=i, ename=e["name"].lower())]
                    targets = e['target']
                    # remove children of target
                    targets = [t for t in targets
                               if not has_ancestor(t, set(targets) - {t})]
                    # drop grammatical isolates
                    targets = [t for t in targets
                               if t in parents]


                    for term in targets:
                        if target != term: # drop frames pointing to self
                            yield tokens[target], rel_uri,  tokens[term]
