##
# @file ent_core.py
# @brief contains EntCore entity - parent core enitity with useful functions
# 
# see class for more information
#
# @section important_functions important functions
# - image and alias extraction
# - date extraction
# - unit conversion
# - latitude and longtitude extraction
#
# @section general_ent_information general entity information
# - ID
# - prefix
# - title
# - aliases
# - redirects
# - description
# - original title
# - images
# - link
#
# description is first sentence extracted from a file passed to the core entity during initialization <br>
# if first sentece is not found in the file it is extracted with the get_first_sentence function <br>
# but first sentece with wikipedia formatting is also stored because it helps with extraction of other information
# 
# @section date_conversion date conversion 
# main function extracting dates is the extract_date function <br>
# other date functions are helper function to the main function and they are not ment to be called
#
# @author created by Jan Kapsa (xkapsa00)
# @date 28.07.2022

from abc import ABCMeta, abstractmethod
import re
from hashlib import md5, sha224
import mwparserfromhell as parser

## 
# @class EntCore
# @brief abstract parent entity
# 
# contains the general information that is shared across all entities and some useful functions
class EntCore(metaclass=ABCMeta):
    # FIXME: this is a bad idea because of multiprocessing 
    counter = 0

    ##
    # @brief initializes the core entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
    @abstractmethod
    def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
        EntCore.counter += 1
        self.d = debugger

        # general information
        self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]
        self.prefix = prefix
        self.title = re.sub(r"\s+\(.+?\)\s*$", "", title)
        self.aliases = ""
        self.redirects = redirects
        self.description = sentence
        self.original_title = title
        self.images = ""
        self.link = link
        self.langmap = langmap

        # extracted data
        self.infobox_data       = data["data"]
        self.infobox_name       = data["name"]
        self.categories         = data["categories"]
        self.first_paragraph    = data["paragraph"]
        self.coords             = data["coords"]
        
        self.first_sentence = ""

        lang = link[8:10]
        if lang == "en":
            if self.first_paragraph:
                self.get_first_sentence(self.first_paragraph)
                self.get_aliases()

            self.extract_image()
    
    ##
    # @brief serializes entity data for output (tsv format)
    # @param ent_data - child entity data that is merged with general data <tsv string>
    # @return tab separated values containing all of entity data <string>
    def serialize(self, ent_data):
        data = "\t".join([
            self.eid,
            self.prefix,
            self.title,
            self.aliases,
            "|".join(self.redirects),
            self.description,
            self.original_title,
            self.images,
            self.link,
            ent_data
        ]).replace("\n", "")
        return data

    # get_aliases
    # get_images
    # get_description

    ##
    # @brief tries to extract the first sentence from the first paragraph
    # @param paragraph - first paragraph of the page <string>
    #
    # removes the wikipedia formatting and assigns the description variable if it is empty
    # but first sentece with wikipedia formatting is also stored because it helps with extraction of other information
    #
    # e.g.: '''Vasily Vasilyevich Smyslov''' (24 March 1921 – 27 March 2010) was a [[Soviet people|Soviet]] ...
    def get_first_sentence(self, paragraph):
        paragraph = paragraph.strip()
        paragraph = re.sub(r"\.({{.*?}})", ".", paragraph)

        pattern = r"('''.*?'''.*?\.)(?:\s*[A-Z][a-z,]+\s[a-z0-9]|\n|$|\]\])"
        m = re.search(pattern, paragraph)
        if m:            
            # maybe use this for extraction
            first_sentence = m.group(1)
            langs = []

            # and this for description
            
            # sub '''
            description = re.sub(r"'{2,3}|&.+;", "", first_sentence)

            # match things inside [[]]
            description = re.sub(r"\[\[[^\[\]]+?\|([^\[\]\|]+?)\]\]", r"\1", description)            
            description = re.sub(r"\[|\]", r"", description)

            for lang in re.finditer(r"({{lang.*?}});?", description):
                langs.append(lang.group(1))

            self.get_lang_aliases(langs)

            # TODO: convert, dates
            
            description = re.sub(r"{{.*?}};?", "", description)
            description = re.sub(r"{|}", "", description)
            description = re.sub(r"\)\)", ")", description)

            description = re.sub(r"\(\s+", "(", description)
            description = re.sub(r"\s+", " ", description)
            description = re.sub(r"\s\(\)\s?", " ", description)

            description = re.sub(r"\s?\(,.*?\)|\s?\(.*?\s+\)", "", description)
            description = re.sub(r"\s+,", ",", description)

            # print(f"{description}\n")
            if self.description == "":
                self.description = description
            self.first_sentence = first_sentence
        else: 
            # print(self.first_paragraph)           
            # print(f"{self.original_title}: error\n")
            pass

    ##
    # @brief extracts an alias in a native language
    # @param langs - aliases in a wikipedia format <array of strings>
    # 
    # e.g.: {{lang-rus|Васи́лий Васи́льевич Смысло́в|Vasíliy Vasíl'yevich Smyslóv}};
    def get_lang_aliases(self, langs):
        if len(langs) > 0:
            for lang in langs:
                lang = re.sub(r"{{lang(?:-|\|)(.*?)}}", r"\1", lang)
                split = lang.split("|")
                code = split[0].split("-")[0]
                if len(code) != 2:
                    if code in self.langmap:
                        code = self.langmap[code].split("|")[0]
                    else:
                        code = "??"
                
                for s in split[1:]:
                    if "=" in s:
                        split.remove(s)

                if len(split) < 2:
                    # self.d.log_message(f"couldn't split lang alias: {split[0]} [{self.link}]")
                    return

                alias = split[1]
                if len(split) > 2:
                    if "{" not in alias:
                        if self.aliases:
                            self.aliases += f"|{alias}#lang={code}"
                        else:
                            self.aliases = f"{alias}#lang={code}"

    ##
    # @brief extracts aliases from the first sentence
    def get_aliases(self):
        title = self.title
        sentence = self.first_sentence

        sentence = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", sentence)
        sentence = re.sub(r"\[|\]", "", sentence)
        
        aliases = []
    
        split = title.split(" ")
        name = split[0]
        surname = split[-1] if len(split) > 1 else ""
        
        # finds all names in triple quates and removes those that match the title 
        aliases = re.findall(r"(?:\"|\()?'''.*?'''(?:\"|\))?", sentence)
        aliases = [re.sub(r"'{3,5}", "", a) for a in aliases]
        aliases = [a for a in aliases if a != title]
        
        title_data = title.split(" ")
        
        # handles born surnames (née)
        born_name = ""
        m = re.search(r".*née\s'''(.*?)'''.*", sentence)
        if m:
            born_name = m.group(1)
        
        # handles aliases in double quotes and brackets
        # surname is added to nicknames as a rule
        patterns = [r"\"(.*?)\"", r"\((.*?)\)"]
        nicknames = []
        for pattern in patterns:
            for i in range(len(aliases)):
                m = re.search(pattern, aliases[i])
                if m:
                    if m.start():
                        cut = f"{aliases[i][:m.start()].strip()} {aliases[i][m.end():].strip()}"
                        aliases[i] = cut
                    else:
                        if i-1 >= 0 and i+1 < len(aliases):
                            cut = f"{aliases[i-1]} {aliases[i+1]}"
                            aliases[i-1] = cut
                            aliases[i+1] = ""
                    nicknames.append(m.group(1))
        
        nicknames = [
            f"{nick} {surname}" for nick in nicknames 
            if f"{nick} {surname}" != title 
            and nick != title
        ]
        
        # remove previously handeled nicknames and born surname
        aliases = [
            item for item in aliases 
            if item 
            and item not in title_data 
            and '"' not in item
            and "(" not in item
            and item != title
        ]
        if born_name and born_name != title:
            aliases = [item for item in aliases if item != born_name]
        
        aliases = [re.sub(r"\(|\)", "", a).strip() for a in aliases]

        aliases += nicknames
        if born_name and born_name != title:
            aliases.append(f"{name} {born_name}")
        
        self.aliases = self.aliases.split("|")
        self.aliases += aliases
        
        # TODO: get aliases from infoboxes
        # keys = ["name", "birth_name", "birthname", "native_name", "nativename", "aliases"]
        # for key in keys:
        #     if key in self.infobox_data and self.infobox_data[key]:
        #         value = self.infobox_data[key]
        #         if value != title and value not in self.aliases:
        #             self.d.log_message(f"{key} -> {value}")

        self.aliases = [re.sub(r"\{\{.*?\}\}", "", a).strip() for a in self.aliases]
        self.aliases = [a for a in self.aliases if a != title]
        self.aliases = [a for a in self.aliases if a != ""]

        self.aliases = "|".join(self.aliases)

        # if self.aliases:
        #     self.d.log_message(f"{'|'.join(self.aliases)}")
        pass

    ##
    # @brief extracts image data from the infobox
    def extract_image(self):
        keys = ["image", "photo", "image_name", "image_flag", "image_coat", "image_map", "map_image", "logo"]

        for key in keys:
            if key in self.infobox_data and self.infobox_data[key] != "":
                image = self.infobox_data[key].replace("\n", "")
                if not image.startswith("http"):
                    image = self.get_images(image)
                    self.images += image if not self.images else "|" + image

    ##
    # @brief removes wikipedia formatting and assigns image paths to the images variable
    # @param image - image data with wikipedia formatting
    def get_images(self, image):
        result = []

        image = re.sub(r"file:", "", image, flags=re.I)
        
        images = []
        
        if re.search(r"\{|\}", image):
            wikicode = parser.parse(image)
            templates = wikicode.filter_templates(wikicode)
            for t in templates:
                params = t.params
                for p in params:
                    if re.search(r"image|photo|[0-9]+", str(p.name), re.I):
                        if re.search(r"\.jpg|\.svg", str(p.value), re.I):
                            images.append(str(p.value))

        if not len(images):
            images.append(image)    
        
        images = [re.sub(r"^(?:\[\[(?:image:)?)?(.*?(?:\.jpg|\.png|\.svg)).*$", r"\1", img, flags=re.I) for img in images]
        images = [img.strip().replace(" ", "_") for img in images]

        result = [self.get_image_path(img) for img in images]

        return "|".join(result)

    ##
    # @brief generates server path from an image name
    # @param image - image name 
    @staticmethod
    def get_image_path(image):
        image_hash = md5(image.encode("utf-8")).hexdigest()[:2]
        image_link = f"wikimedia/commons/{image_hash[0]}/{image_hash}/{image}"
        return image_link
