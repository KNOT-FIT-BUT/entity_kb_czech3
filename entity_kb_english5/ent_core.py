"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntCore', jež je rodičovskou třídou pro podtřídy entit.
Poznámka: inspirováno projektem entity_kb_czech3
"""

from abc import ABCMeta, abstractmethod
import re
from hashlib import md5, sha224

class EntCore(metaclass=ABCMeta):
    """
    abstraktní rodičovská třída, ze které dědí všechny entity
    instanční atributy:
        title       - název entity
        prefix      - prefix entity
        eid         - ID entity
        link        - odkaz na Wikipedii
        aliases     - alternativní pojmenování entity
        description - stručný popis entity
        images      - absolutní cesty k obrázkům Wikimedia Commons
    třídní atributy:
        counter     - počítadlo instanciovaných objektů z odvozených tříd
    metody:
        get_data            - extrahuje infobox, paragraf a další hodnoty ze stránky
        get_first_sentence  - extrahuje první větu
        extract_image       - extrahuje obrázky
        get_image_path      - vrátí cesty k obrázkům Wikimedia Commons
        get_coordinates     - pokusí se vrátit zeměpisnou šířku a výšku 
        convert_units       - konverze jednotek
    """

    counter = 0

    @abstractmethod
    def __init__(self, title, prefix, link):
        """
        Inicializuje třídu EntCore
        Parametry:
        title   - název stránky
        prefix  - prefix entity
        link    - odkaz na Wikipedii
        """
        EntCore.counter += 1

        # vygenerování hashe
        self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]
        self.original_title = title
        self.title = re.sub(r"\s+\(.+?\)\s*$", "", title)
        self.prefix = prefix
        self.link = link
        self.images = ""

        # TODO: this should be dictionary of dictionaries for multiple infoboxes
        # that way I can also save the infobox name
        self.infobox_data = dict()
        self.infobox_name = ""
        self.categories = []
        self.first_paragraph = ""
        self.first_sentence = ""
        self.short_description = ""
    
    def serialize(self, ent_data):
        """
        serializuj entitu pro výstup
        """
        return "\t".join([
            self.eid,
            self.prefix,
            self.title,
            "",
            "",
            "",
            self.original_title,
            "",
            self.link,
            ent_data
        ])

    def get_data(self, content):
        """
        extrahuje infobox, paragraf a další hodnoty ze stránky
        """
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
        
        if (self.first_paragraph):
            self.first_sentence = self.get_first_sentence(self.first_paragraph)

        self.extract_image()

    # WIP first sentence / description extraction
    #@staticmethod
    def get_first_sentence(self, paragraph):
        """
        extrahuje první větu
        """
        pattern = r"('''.*?\.)(?:\s?[A-Z][a-z]+|\n|$)"
        m = re.match(pattern, paragraph)
        if m:            
            # maybe use this for extraction
            first_sentence = m.group(1)

            # # and this for description
            
            # # sub '''
            # description = re.sub(r"'{2,3}|&.+;", "", first_sentence)

            # # match things inside [[]] and {{}}
            # description = re.sub(r"\[\[[^\[\]]+?\|([^\[\]\|]+?)\]\]", r"\1", description)            
            # description = re.sub(r"\[|\]", r"", description)

            # description = re.sub(r"\{\{[^\{\}]+?\|([^\{\}\|]+?)\}\}", r"\1", description)            
            # description = re.sub(r"\{|\}", r"", description)            
            
            # print(f"{self.original_title}: {description}\n")
            self.first_sentence = first_sentence

    # WIP image extraction
    def extract_image(self):
        """
        extrahuje obrázky
        """
        if "image" in self.infobox_data and self.infobox_data["image"] != "":
            image = self.infobox_data["image"]
            image = self.get_image_path(image)
            #print(image)
            self.images += image if not self.images else "|" + image

    @staticmethod
    def get_image_path(image):
        """
        Převádí název obrázku na absolutní cestu Wikimedia Commons.

        Parametry:
        image - název obrázku (str)
        """

        # remove templates with descriptions from image path
        image = re.sub(r"{{.*$", "", image)
        image = re.sub(r"\s*\|.*$", "", image).replace("}", "").strip().replace(" ", "_")
        image_hash = md5(image.encode("utf-8")).hexdigest()[:2]
        image = "wikimedia/commons/" + image_hash[0] + "/" + image_hash + "/" + image

        return image

    # returns latitude, longtitude
    @staticmethod
    def get_coordinates(format):
        """
        pokusí se vrátit zeměpisnou šířku a výšku 
        """
        # matching coords format with directions
        # {{Coord|59|56|N|10|41|E|type:city}}
        pattern = r"([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(N|S)\|([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(E|W)"
        m = re.search(pattern, format)
        if m:
            data = [x for x in m.groups() if x != None]
            data = [data[:int(len(data)/2)], data[int(len(data)/2):]]
            
            coords = [0, 0]
            
            # conversion calculation
            for d in range(2):
                for i in range(len(data[d])-1):
                    coords[d] += float(data[d][i]) / 60*i if i != 0 else float(data[d][i])
                coords[d] = round(coords[d], 5)
                if data[d][-1] in ("S", "W"):
                    coords[d] *= -1
                
            #print(f"latitude: {coords[0]}\nlongtitude: {coords[1]}\n")
            return (str(coords[0]), str(coords[1]))
        
        # matching coords format without directions (direct latitude and longtitude)
        # {{coord|41.23250|-80.46056|region:US-PA|display=inline,title}}
        pattern = r"{{.*\|([0-9.-]+)\|\s*?([0-9.-]+).*}}"
        m = re.search(pattern, format)
        if m:
            #print(f"latitude: {m.group(1)}\nlongtitude: {m.group(2)}\n")
            return (m.group(1), m.group(2))
            
        #print(f"Error: coords format error ({format})")
        return (None, None)

    # converts units
    # TODO: add more units
    @staticmethod
    def convert_units(number, unit, round_to=2):
        """
        konverze jednotek
        """
        
        number = float(number)
        unit = unit.lower()

        SQMI_TO_KM2 = 2.589988
        FT_TO_M = 3.2808
        MI_TO_KM = 1.609344
        CUFT_TO_M3 = 0.028317

        accepted_untis = ["km2", "km", "m", "meters", "m3", "m3/s"]
        if unit in accepted_untis:
            return str(number if number % 1 != 0 else int(number))

        if (unit == "sqmi"):
            number = round(number * SQMI_TO_KM2, round_to)
        elif (unit == "mi"):
            number = round(number * MI_TO_KM,round_to)
        elif (unit in ["ft", "feet"]):
            number = round(number / FT_TO_M, round_to)
        elif(unit in ["cuft/s", "cuft"]):
            number = round(number * CUFT_TO_M3,round_to)
        else:
            #print(f"Error: unit conversion error ({unit})")
            return ""

        return str(number if number % 1 != 0 else int(number))