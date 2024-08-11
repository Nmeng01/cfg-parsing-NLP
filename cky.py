"""
COMS W4705 - Natural Language Processing - Fall 2023
Homework 2 - Parsing with Probabilistic Context Free Grammars 
Daniel Bauer
"""
import math
import sys
from collections import defaultdict
import itertools
from grammar import Pcfg

### Use the following two functions to check the format of your data structures in part 3 ###
def check_table_format(table):
    """
    Return true if the backpointer table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Backpointer table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and \
          isinstance(split[0], int)  and isinstance(split[1], int):
            sys.stderr.write("Keys of the backpointer table must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of backpointer table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            bps = table[split][nt]
            if isinstance(bps, str): # Leaf nodes may be strings
                continue 
            if not isinstance(bps, tuple):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Incorrect type: {}\n".format(bps))
                return False
            if len(bps) != 2:
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Found more than two backpointers: {}\n".format(bps))
                return False
            for bp in bps: 
                if not isinstance(bp, tuple) or len(bp)!=3:
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has length != 3.\n".format(bp))
                    return False
                if not (isinstance(bp[0], str) and isinstance(bp[1], int) and isinstance(bp[2], int)):
                    print(bp)
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has incorrect type.\n".format(bp))
                    return False
    return True

def check_probs_format(table):
    """
    Return true if the probability table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Probability table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and isinstance(split[0], int) and isinstance(split[1], int):
            sys.stderr.write("Keys of the probability must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of probability table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            prob = table[split][nt]
            if not isinstance(prob, float):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a float.{}\n".format(prob))
                return False
            if prob > 0:
                sys.stderr.write("Log probability may not be > 0.  {}\n".format(prob))
                return False
    return True



class CkyParser(object):
    """
    A CKY parser.
    """

    def __init__(self, grammar): 
        """
        Initialize a new parser instance from a grammar. 
        """
        self.grammar = grammar

    def is_in_language(self,tokens):
        """
        Membership checking. Parse the input tokens and return True if 
        the sentence is in the language described by the grammar. Otherwise
        return False
        """
        # TODO, part 2
        parsetbl = [[set() for _ in range(len(tokens) + 1)] for _ in range(len(tokens) + 1)]
        for i in range(len(tokens)):
            parsetbl[i][i+1] = set(r[0] for r in self.grammar.rhs_to_rules[(tokens[i],)])
        
        for x in range(2, len(tokens)+1):
            for y in range(len(tokens)-x+1):
                j = y + x
                for z in range(y+1, j):
                    for rhs, rlist in self.grammar.rhs_to_rules.items():
                        if len(rhs) > 1 and rhs[0] in parsetbl[y][z] and rhs[1] in parsetbl[z][j]:
                            for r in rlist: parsetbl[y][j].add(r[0])
                        
        return self.grammar.startsymbol in parsetbl[0][len(tokens)]
       
    def parse_with_backpointers(self, tokens):
        """
        Parse the input tokens and return a parse table and a probability table.
        """
        # TODO, part 3
        table= {}
        probs = {}
        for x in range(len(tokens) + 1):
            for y in range(len(tokens) + 1):
                table[(x,y)] = {}
                probs[(x,y)] = {}
        
        for i in range(len(tokens)):
            for r in self.grammar.rhs_to_rules[(tokens[i]),]:
                if r[0] not in probs[(i, i+1)] or probs[(i, i+1)][r[0]] < r[2]:
                    table[(i, i+1)][r[0]] = r[1][0]
                    probs[(i, i+1)][r[0]] = math.log2(r[2])

        
        for x in range(2, len(tokens)+1):
            for y in range(len(tokens)-x+1):
                j = x+y
                for z in range(y+1, j):
                    for rhs, rlist in self.grammar.rhs_to_rules.items():
                        if len(rhs) > 1 and rhs[0] in table[(y,z)] and rhs[1] in table[(z, j)]:
                            for r in rlist: 
                                curr_prob = probs[(y, z)][rhs[0]] + probs[(z,j)][rhs[1]] + r[2] 
                                if r[0] not in probs[(y,j)] or curr_prob > probs[(y,j)][r[0]]:
                                    table[(y,j)][r[0]] = ((rhs[0], y, z), (rhs[1], z, j))
                                    probs[(y,j)][r[0]] = curr_prob

        return table, probs


def get_tree(chart, i,j,nt): 
    """
    Return the parse-tree rooted in non-terminal nt and covering span i,j.
    """
    # TODO: Part 4
    if i == j-1:
        return (nt, chart[(i,j)][nt])
    else:
        left = chart[(i,j)][nt][0]
        right = chart[(i,j)][nt][1]
        return (nt, get_tree(chart, left[1], left[2], left[0]), get_tree(chart, right[1], right[2], right[0]))
 
       
if __name__ == "__main__":
    
    with open('atis3.pcfg','r') as grammar_file: 
        grammar = Pcfg(grammar_file) 
        parser = CkyParser(grammar)
        toks =['flights', 'from','miami', 'to', 'cleveland','.'] 
        print(parser.is_in_language(toks))
        table,probs = parser.parse_with_backpointers(toks)
        print(check_table_format(table))
        print(check_probs_format(probs))
        print(get_tree(table, 0, len(toks), grammar.startsymbol))
        
