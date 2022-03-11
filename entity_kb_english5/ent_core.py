"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntCore', jež je rodičovskou třídou pro podtřídy entit.
Poznámka: inspirováno projektem entity_kb_czech3
"""

from abc import ABCMeta, abstractmethod
import re

class EntCore(metaclass=ABCMeta):
    """
    Abstraktní rodičovská třída, ze které dědí všechny entity.
    Instanční atributy:
    title       - název entity (str)
    prefix      - prefix entity (str)
    eid         - ID entity (str)
    link        - odkaz na Wikipedii (str)
    aliases     - alternativní pojmenování entity (str)
    description - stručný popis entity (str)
    images      - absolutní cesty k obrázkům Wikimedia Commons (str)
    Třídní atributy:
    counter     - počítadlo instanciovaných objektů z odvozených tříd
    Metody:
    del_redundant_text(text)    - odstraňuje přebytečné části textu, ale pouze ty, které jsou společné pro všechny získávané údaje
    get_image(image)            - převádí název obrázku na absolutní cestu Wikimedia Commons
    """
    @abstractmethod
    def __init__(self, title, prefix, link):
        """
        Inicializuje třídu 'EntCore'.
        Parametry:
        title   - název stránky (str)
        prefix  - prefix entity (str)
        link    - odkaz na Wikipedii (str)
        """
        self.title = " ".join(title.split())
        self.prefix = prefix
        # TODO: eid
        self.link = link

        # TODO: this should be dictionary of dictionaries for multiple infoboxes
        # that way I can also save the infobox name
        self.infobox_data = dict()
        self.categories = []
        self.first_paragraph = ""
        self.short_description = ""
    
    def get_data(self, content):
                
        lines = content.splitlines()
        
        infobox = False
        paragraph_bounds = False
        description_found = False

        # TODO: optimize this
        for line in lines:
            
            if description_found == False:
                pattern = r"^{{[s|S]hort description\|([^\|]+)(?:\|.+)?}}$"
                match = re.search(pattern, line)
                if match:
                    description_found = True
                    self.short_description = match.group(1)

            # extract infobox / infoboxes
            if line.startswith("{{Infobox"):
                infobox = True
                # TODO: infobox name could be useful
            elif line.startswith("}}") and infobox == True:
                infobox = False
            elif infobox == True:
                # example: "| name = Edward Andrade"
                pattern = r"\|\s*?(\w*)\s*?=\s*(.*)"
                match = re.match(pattern, line)
                if match:
                    self.infobox_data[match.group(1)] = match.group(2)            

            # extract first paragraph
            if line.startswith("'''"):
                paragraph_bounds = True
                self.first_paragraph += line
            elif line.startswith("==") and paragraph_bounds == True:
                paragraph_bounds = False
            elif paragraph_bounds == True:
                self.first_paragraph += line
            
            # extract categories
            if line.startswith("[[Category:"):
                self.categories.append(line[11:-2].strip())