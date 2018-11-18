#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje parser XML dumpu Wikipedie.
Identifikuje a extrahuje typy infoboxu související s osobami a zapíše je do zvláštního souboru.
"""

import xml.etree.cElementTree as CElTree
import re
from os import remove
import argparse


ib_types = set()

# parsuje argumenty zadané při spuštění
console_args_parser = argparse.ArgumentParser()
console_args_parser.add_argument("src_file", nargs="?", default="/mnt/minerva1/nlp/corpora_datasets/monolingual/czech/wikipedia/cswiki-latest-pages-articles.xml", type=str, help="zdrojový soubor")
console_args = console_args_parser.parse_args()

# parsuje XML dump Wikipedie a prochází jednotlivé stránky
# založeno na: http://effbot.org/zone/element-iterparse.htm
context = CElTree.iterparse(console_args.src_file, events=("start", "end"))
context = iter(context)
event, root = next(context)

for event, elem in context:
    if event == "end":
        if "page" in elem.tag:
            ib_title = ""

            for child in elem:
                if "title" in child.tag:
                    if not child.text.startswith("Šablona:"):
                        continue
                    ib_title = child.text
    
                if ib_title:
                    if "revision" in child.tag:
                        for grandchild in child:
                            if "text" in grandchild.tag:
                                if re.search(r"\[\[\s*Kategorie:\s*Infoboxy\s+lidí", grandchild.text):
                                    ib_re = re.search(r"^Šablona:Infobox[\-–—−\s]+(.+)$", ib_title)
                                    if ib_re:
                                        ib_type = ib_re.group(1).replace("/doc", "").strip().lower()
                                        if "etnická skupina" in ib_type or "předkové" in ib_type:  # nesouvisí s osobami
                                            continue
                                        ib_types.add(ib_type)
        root.clear()

# odstraní soubor před začátkem extrakce, pokud nějaká existuje
try:
    remove("person_infoboxes")
except OSError:
    pass

# zápis typů infoboxu do souboru
with open("person_infoboxes", "a", encoding="utf-8") as fl:
    for ib in ib_types:
        fl.write(ib + "\n")
