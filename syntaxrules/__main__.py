"""
Apply transformation rules to a syntax (dependency) graph.

A Sparql server should be listening at http://localhost:3030/x

See: http://github.com/vanatteveldt/syntaxrules

Examples:
(For testing, feel free to use syntaxrules/rulesets/sources_nl.json as rules
 and tests/sources_nl_test.json as input)
- Write the results as a complete NAF json file
  python -m syntaxrules -o out.json -i parse.json rules.json
- Print the found roles as json with words
  python -m syntaxrules -rw rules.json < parse.json
- Visualize the graph into out.png (using -o or using stdout)
  python -m syntaxrules -vo out.png -i parse.json rules.json
  python -m syntaxrules -v rules.json < parse.json > out.png
- Visualize the graph into out.dot (using -o or using stdout and -f)
  python -m syntaxrules -vo out.dot -i parse.json rules.json
  python -m syntaxrules -vf dot rules.json < parse.json
"""

import json
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import sys
import os.path

import syntaxrules

parser = ArgumentParser(prog="syntaxrules", epilog=__doc__,
                        formatter_class=RawDescriptionHelpFormatter)
parser.add_argument("ruleset", help="Name of the file containing the  "
                    "rule set (in json), Use '-' to not apply any rules")
parser.add_argument("--input", "-i", help="Name of the inputfile "
                    "(in SAF json) to use. "
                    "If omitted, input will be read from stdin")
parser.add_argument("--output", "-o",
                    help="Output file. If not given, will write to stdout")
parser.add_argument("--visualize", "-v", action='store_true',
                    help="Output results as a network graph (png image)")
parser.add_argument("--words", "-w", action='store_true',
                    help="Use words in output instead of token ids")
parser.add_argument("--roles-only", "-r", action='store_true',
                    help="Output roles only. By default, output is the "
                    "complete SAF json representation of the document")
parser.add_argument("--visualize-format", "-f", action='store',
                    help="Format for the visualization, e.g. png or dot. "
                    "If omitted, use output extension or default to png")
parser.add_argument("--sentence", "-s", action='store', default=1, type=int,
                    help="ID of the sentence to use")

args = parser.parse_args()
# prepare input and output files
input_file = sys.stdin if args.input is None else open(args.input)
saf= json.load(input_file)
outfile = (sys.stdout if args.output is None
           else open(args.output, "w"))

# get the syntax tree
soh = syntaxrules.SOHServer(url="http://localhost:3030/x")
t = syntaxrules.SyntaxTree(soh)
t.load_saf(saf, sentence_id=args.sentence)

# apply the rules
if args.ruleset != '-':
    ruleset = json.load(open(args.ruleset))
    t.apply_ruleset(ruleset)


# roles
roles = list(t.get_relations())
if args.words:
    words = {t['id']: t['word'] for t in saf['tokens']}
    def _convert(val):
        # recursively replace all (!) integers x by words[x] in a json dict
        if isinstance(val, int):
            return words[val]
        elif isinstance(val, list):
            return [_convert(v) for v in val]
        elif isinstance(val, dict):
            return {k: _convert(v) for (k, v) in val.iteritems()}
        return val
    roles = _convert(roles)

# output
if args.roles_only:
    json.dump(roles, outfile, indent=2)
elif args.visualize:
    if args.visualize_format is None and args.output is not None:
        format = os.path.splitext(args.output)[1][1:]
    elif args.visualize_format is None:
        format = "png"
    else:
        format = args.visualize_format
    g = t.get_graphviz(triple_args_function=syntaxrules.VIS_GREY_REL)
    g.draw(outfile, prog="dot", format=format)
else:
    saf['roles'] = roles
    json.dump(saf, outfile, indent=2)
