#!/usr/bin/python3

import os
import pathlib
import re
import sys

# Reservation -- begins with "reserve", ends with ";"
# Definition -- begins with "definition", ends with "end;"
# Registration -- begins with "registration", ends with "end;"
# Notation -- begins with "notation", ends with "end;"
# Theorem -- begins with "theorem", ends with ";"
# Scheme -- begins with "scheme", ends with ";"
# Auxiliary item = statement ("lemmas") or private definitions (deffunc, defpred)
notation = {" \ ": ' \setminus ',
            ' \/ ': ' \cup ',
            " /\\ ": ' \cap ',
            " \\+\\ ": ' \dotminus ',
            'c<': '\propersubset',
            ' c= ': ' \subset ',
            'are_c=-comparable': '\\areComparable',
            " bool ": " \\bool ",
            " meets ": " \\meets ",
            " misses ": " \\misses ",
            ' {}': ' \emptyset',
            ' <> ': " \\neq ",
            " not ": " \\neg ",
            " & ": " \\land ",
            " for ": " \\forall ",
            " ex ": " \\ex ",
            " implies ": " \\implies ",
            " or ": " \\lor ",
            " st ": " \\st ",
            " iff ": " \\iff ",
            " holds " : " \\holds ",
            " is " : " \\is ",
            " it " : " \\IT ",
            " being " : " \\being ",
            " the " : " \\THE "
            }

class TextItem:
    def __str__(self):
        return "TextItem.__str__ not implemented"

class Theorem:
    def __init__(self, statement):
        self.statement = statement
    def __str__(self):
        return self.statement
    def latexify(self):
        idx = self.statement.find("\n")+1
        s = self.statement[idx:]
        for mizar,latex in notation.items():
            s = s.replace(mizar,latex)
        return '\\begin{theorem}'+"\n"+s[:-1]+".\n"+'\end{theorem}'

class Reservation:
    def __init__(self, variables, mode):
        self.variables = []
        for var in map(lambda x: x.strip(), variables):
            self.variables.append(var)
        self.mode = mode
    def __str__(self):
        coll = []
        for var in self.variables:
            coll.append(var)
        return "reserve "+(",".join(coll))+" for "+self.mode
    def latexify(self):
        coll = []
        for var in self.variables:
            coll.append('$'+var+'$')
        return "Let "+(", ".join(coll))+" denote a "+self.mode+"."

class LociDeclaration:
    def __init__(self, qualified_vars, conds):
        self.vars = qualified_vars
        self.conds = conds
        
class Register:
    def __init__(self, statements):
        self.statements = statements
    
def article_path(name):
    if name.startswith('--file='):
        filename = name[len("--file="):]
        return filename.strip()
    elif name.startswith('-f'):
        if '=' == name[2]:
            filename = name[3:]
        else:
            filename = name[2:]
        return filename.strip()
    else:
        filename = name.lower()+".abs"
        mizfiles = os.environ.get('MIZFILES')
        return str(pathlib.PurePath(mizfiles, "abstr", filename))

def read_article(article_id):
    f = open(article_path(article_id))
    txt = f.read()
    f.close()
    txt = re.sub('\n::[^\n]+\n', '\n', txt)
    start = txt.find("\nbegin") + len("\nbegin")
    return txt[start:].lstrip()

# parse_reservation("reserve x,y for set;") == [Reservation(["x","y"],"set")]
# parse_reservation("reserve x,y for set, a,b for Function")
# == [Reservation(["x","y"],"set"), Reservation(["a","b"],"Function")]
def parse_reservation(item):
    results = []
    start = len("reserve")
    mid = item.find(" for ", start)
    end = item.find(",", mid+len(" for "))
    while end != -1:
        r = Reservation(item[start:mid].split(","), item[mid+len(" for "):end])
        results.append(r)
        start = end+1
        mid = item.find(" for ", start)
        end = item.find(",", mid + len(" for "))
    item.find(";", mid + len(" for "))
    r = Reservation(item[start:mid].split(","), item[mid+len(" for "):end])
    results.append(r)
    return results

def read_reservations(txt):
    next_txt = txt.lstrip();
    results = [];
    while next_txt.lstrip().startswith("reserve"):
        start = next_txt.find("reserve");
        end = next_txt.find(";") + 1;
        item = next_txt[start:end];
        results = results + parse_reservation(item)
        next_txt = next_txt[end:];
    return (next_txt.lstrip(), results)

def read_theorems(txt):
    next_txt = txt.lstrip();
    results = [];
    while next_txt.lstrip().startswith("theorem"):
        start = next_txt.find("theorem");
        end = next_txt.find(";") + 1;
        item = Theorem(next_txt[start:end]);
        results.append(item);
        next_txt = next_txt[end:];
    return (next_txt.lstrip(),results)

def read_begin(txt):
    idx = txt.find("\n") #+ 1;
    return txt[idx:]

def parse_items(txt):
    results = [] # [[TextItem]]
    while '' != txt.lstrip():
        next_item_type = re.match(r"\S*", txt, re.UNICODE).group(0)
        print("NEXT = "+next_item_type, file=sys.stderr)
        if "reserve" == next_item_type:
            (next_txt, item) = read_reservations(txt)
            txt = next_txt
            results.append(item)
        elif "theorem" == next_item_type:
            (next_txt, item) = read_theorems(txt)
            txt = next_txt
            print("Theorem ended with, '"+txt[:20]+"'", file=sys.stderr)
            results.append(item)
        elif "begin" == next_item_type:
            next_txt = read_begin(txt).lstrip()
            print("Begin found, '"+next_txt[:25]+"'", file=sys.stderr)
            txt = next_txt
        elif next_item_type.startswith('::'):
            idx = txt.find("\n") + 1;
            txt = txt[idx:]
        else:
            if '' == next_item_type.lstrip():
                return results
            print("ERROR cannot parse: '", next_item_type, "'")
            exit()
    return results

def transcribe_cluster(cluster):
    left_column = ""
    right_column = ""
    for item in cluster:
        left_column = left_column + "\n" + item.latexify() + "\n"
        right_column = right_column + "\n" + str(item) + "\n"
    return "\\switchcolumn*\\ensurevspace{5cm}\n"+left_column+"\n\\switchcolumn\n\n\\begin{mizar}"+right_column+"\\end{mizar}\n"

def partition(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def transcribe(article_id):
    txt = read_article(article_id)
    results = parse_items(txt)
    for chunks in results:
        for cluster in list(partition(chunks, 5)):
            print(transcribe_cluster(cluster))
    
def main():
    for arg in sys.argv[1:]:
        transcribe(arg)

if __name__ == '__main__':
    main()
