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
        self.infobox_name = ""
        self.categories = []
        self.first_paragraph = ""
        self.short_description = ""
    
    def get_data(self, content):
        
        lines = content.splitlines()
        
        infobox = False
        indentation = 0
        level = 0
        key = ""
        value = ""

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
                self.infobox_name = line[len("{{Infobox"):].strip()
                infobox = True
            elif infobox == True:
                line = line.strip()
                for i in range(len(line)):
                    if level == 0:
                        if line[i] == "|":
                            level = 1
                    elif level == 1:
                        if line[i] == "=":
                            level = 2
                        else:
                            key += line[i]
                    elif level == 2:
                        
                        if line[i] == "{":
                            indentation += 1
                        elif line[i] == "}":
                            indentation -= 1
                            
                        if line[i] == "|" and indentation == 0 and i == 0:
                            self.infobox_data[key.strip()] = value.strip()
                            key = ""
                            value = ""
                            level = 1
                        elif indentation < 0:
                            self.infobox_data[key.strip()] = value.strip()
                            infobox = False
                            break
                        else:
                            value += line[i]         

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