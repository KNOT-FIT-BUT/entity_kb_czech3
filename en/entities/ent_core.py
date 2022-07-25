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
# @date 15.07.2022

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

        # vygenerování hashe
        self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]
        self.original_title = title
        self.title = re.sub(r"\s+\(.+?\)\s*$", "", title)
        self.prefix = prefix
        self.link = link
        self.images = ""
        self.langmap = langmap
        self.redirects = redirects

        self.infobox_data = data["data"]
        self.infobox_name = data["name"]
        self.categories = data["categories"]
        self.first_paragraph = data["paragraph"]
        self.first_sentence = ""
        self.description = sentence
        self.coords = data["coords"]
        self.aliases = []

        if (self.first_paragraph):
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
            "|".join(self.aliases),
            "|".join(self.redirects),
            self.description,
            self.original_title,
            self.images,
            self.link,
            ent_data
        ]).replace("\n", "")
        return data

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
    # @param lags - aliases in a wikipedia format <array of strings>
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
                        self.aliases.append(f"{alias}#lang={code}")

    ##
    # @brief extracts aliases from the first sentence         
    def get_aliases(self):
        if self.first_sentence:
            self.d.log_message(f"{self.title}: {self.first_sentence}")
            string = self.first_sentence
            name = ""
            aliases = []
            
            string = re.sub(r"\[\[[^\[\]]*?\|([^\[\]]*?)\]\]", r"\1", string)
            string = re.sub(r"\[|\]", "", string)

            # "alias" in the name
            m = re.search(r"'''(.*\"(.*)\"\s+[\w'\.\s]+?)'''", string)
            if m:
                alias = m.group(2)
                alias = re.sub(r"\'", "", alias)
                name = m.group(1)
                name = re.sub(r"\".*?\"|'", "", name)
                name = re.sub(r"\s+", " ", name)
                split = name.split(" ")
                i = -1
                surname = split[i]
                while "." in surname and abs(i) != len(split):
                    i -= 1
                    surname = split[i]
                alias += f" {surname}"
                aliases.append(alias)
                string = string[m.end():]
            
            # normal name
            if not name:
                m = re.search(r"'''(.*?)'''", string)
                if m:
                    name = m.group(1)
                    string = string[m.end():]
            
            # all other aliases in the sentence
            string = string.strip()
            if len(string) > 0:
                arr = re.findall(r"'''(.*?)'''", string)
                for s in arr:
                    aliases.append(s)
            
            if name != self.title:
                aliases.append(name)

            for a in aliases:
                if a == self.title:
                    aliases.remove(a)
                self.aliases.append(a)

            # self.d.log_message(f"{self.aliases}")
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

    ##
    # @brief extracts the latitude and longtitude from a wikipedia formated string
    # @param format - wikipedia formated string
    # @return latitude, longtitude
    # 
    # e.g.: {{Coord|59|56|N|10|41|E|type:city}}
    def get_coordinates(self, format):
        # matching coords format with directions
        # {{Coord|59|56|N|10|41|E|type:city}}
        format = re.sub(r"\s", "", format)
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
        pattern = r"{{.*\|([0-9.-]+)\|([0-9.-]+).*}}"
        m = re.search(pattern, format)
        if m:
            #print(f"latitude: {m.group(1)}\nlongtitude: {m.group(2)}\n")
            return (m.group(1), m.group(2))
        
        if re.search(r"[Cc]oords?missing", format):
            return (None, None)

        self.d.log_message(f"coords format no match ({format}) [{self.link}]")
        return (None, None)

    ##
    # @brief converts units to metric system
    # @param number - number to be converted <string>
    # @param unit - unit abbreviation
    # @param round_to - to how many decimal points will be rounded to (default: 2)
    # @return converted rounded number as a string
    def convert_units(self, number, unit, round_to=2):
        try:
            number = float(number)
        except:
            self.d.log_message(f"couldn't conver string to float: {number}")
            return ""
        unit = unit.lower()

        SQMI_TO_KM2 = 2.589988
        HA_TO_KM2 = 0.01
        ACRE_TO_KM2 = 0.00404685642
        M2_TO_KM2 = 0.000001
        MI2_TO_KM2 = 2.589988
        FT_TO_M = 3.2808
        MI_TO_KM = 1.609344
        CUFT_TO_M3 = 0.028317
        FT3_TO_M3 = 0.0283168466
        L_TO_M3 = 0.001

        accepted_untis = ["sqkm", "km2", "km²", "km", "m", "meters", "metres", "m3", "m3/s", "m³/s"]
        if unit in accepted_untis:
            return str(number if number % 1 != 0 else int(number))

        if unit == "sqmi":
            number = round(number * SQMI_TO_KM2, round_to)
        elif unit in ("mi", "mile", "miles"):
            number = round(number * MI_TO_KM,round_to)
        elif unit in ("ft", "feet"):
            number = round(number / FT_TO_M, round_to)
        elif unit in ("cuft/s", "cuft"):
            number = round(number * CUFT_TO_M3,round_to)
        elif unit == "ft3/s":
            number = round(number * FT3_TO_M3, round_to)
        elif unit == "l/s":
            number = round(number * L_TO_M3, round_to)
        elif unit == "ha":
            number = round(number * HA_TO_KM2, round_to)
        elif unit in ("acres", "acre"):
            number = round(number * ACRE_TO_KM2, round_to)
        elif unit == "m2":
            number = round(number * M2_TO_KM2, round_to)
        elif unit == "mi2":
            number = round(number * MI2_TO_KM2, round_to)
        else:
            self.d.log_message(f"Error: unit conversion error ({unit}) [{self.link}]")
            return ""

        return str(number if number % 1 != 0 else int(number))

    ##
    # @brief tries to conver a string to a date with YYYY-MM-DD
    # @param data - string containing a date to be converted
    # @return array with 2 ordered dates
    # 
    # e.g.: example of return values: ["", ""], ["1952-07-23", ""], ["1952-07-23", "1999-04-27"]
    #
    # if the date is BC a minus sign is added before the year <br>
    # unknown values are substituted with question marks - e.g.: 1952-??-?? is a valid date (only the year was extracted) <br>
    # fictional dates are not accounted for <br>
    def extract_date(self, data):
        wikicode = parser.parse(data)
        templates = wikicode.filter_templates()
        
        if len(templates) > 0:
            new_templates = []
            for t in templates:
                if re.search(r"date|death|birth|dda|d-da|b-da", str(t), re.I) and not re.search(r"citation|note", str(t.name), re.I):
                    new_templates.append(t)

            templates = new_templates

            if len(templates) == 0:
                string = wikicode.strip_code()
                templates = wikicode.filter_templates()
                for t in templates:
                    params = t.params
                    for p in params:
                        string += f" {str(p.value)}"
                return [self.parse_no_template(string.strip()), ""]

            template = templates[-1]

            if "based on age" in str(template).lower():
                # invalid template
                # TODO: log?
                return ["", ""]
            
            params = template.params
            date = []

            # filter empty fields, mf and df
            for p in params:
                param = p.value.strip()			
                if param != "" and not param.startswith("mf=") and not param.startswith("df=") and re.search(r".*?[0-9].*?", param):
                    date.append(param)

            return self.order_dates(self.get_date(date, str(template.name)))            
        

        return [self.parse_no_template(data), ""]

    ##
    # @brief splits the date into 2 depending on the wikipedia format
    # @param date - array of date values (year, month, day)
    # @param name - wikipedia format name
    # @return array with 2 values (value is either a date or left empty)
    #
    # date extraction helper function
    def get_date(self, date, name):
        result = []

        if len(date) > 3 or re.search(r".*?(?:death(?:-| )(?:date|year) and age|dda|d-da).*?", name, re.I):
            # split dates
            if len(date) % 2 != 0:
                return ["", ""]
            result.append(self.parse_date(date[:int(len(date)/2)]))
            result.append(self.parse_date(date[int(len(date)/2):]))
        else:
            result.append(self.parse_date(date))
            result.append("")

        return result

    ##
    # @brief determines the date format and calls the appropriate function
    # @param date - array of date values
    # @return date in YYYY-MM-DD format
    #
    # date extraction helper function
    def parse_date(self, date):
        if len(date) < 1:
            return ""
        
        for item in date:
            if not item.isnumeric():
                return self.parse_string_format(item)
        return self.parse_num_format(date)

    ##
    # @brief deals with the numerical date format
    # @param array - array of date values
    # @return date in YYYY-MM-DD format
    # 
    # e.g: {{Birth date|1962|1|16}}
    #
    # date extraction helper function
    def parse_num_format(self, array):
        # e.g.: ['1919', '5'] -> 1919-05-??
        if len(array) > 3:
            # TODO: log invalid
            return ""

        while len(array) < 3:
            array.append("??")

        for i in range(len(array)):
            if array[i].isnumeric():
                if int(array[i]) < 10 and len(array[i]) == 1:
                    array[i] = f"0{array[i]}"
        
        return "-".join(array)
    
    ##
    # @brief deals with the string date format
    # @param string - date
    # @return date in YYYY-MM-DD format
    # 
    # e.g.: {{Birth date|January 16, 1962}}
    #
    # date extraction helper function
    def parse_string_format(self, string):     
        months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        date = []

        # month first
        match = re.search(r"^([a-z]+)[^0-9a-z]+?([0-9]+)[^0-9a-z]+?(-?[0-9]+)", string, re.I)
        if match:
            groups = list(match.groups())
            if groups[0].lower() in months:			
                groups[0] = str(months.index(groups[0].lower())+1)
                for i in range(len(groups)):
                    if groups[i].isnumeric():
                        if 0 < int(groups[i]) < 10 and len(groups[i]) == 1:
                            groups[i] = f"0{groups[i]}"
                date.append(groups[2])
                date.append(groups[0])
                date.append(groups[1])
                return "-".join(date)

        # day first
        match = re.search(r"^([0-9]+)[^\(\)0-9]+?([a-z]+)[^\(\)]+?(-?[0-9]+)", string, re.I)
        if match:
            groups = list(match.groups())
            if groups[1].lower() in months:	
                groups[1] = str(months.index(groups[1].lower())+1)
                for i in range(len(groups)):
                    if groups[i].isnumeric():
                        if 0 < int(groups[i]) < 10 and len(groups[i]) == 1:
                            groups[i] = f"0{groups[i]}"
                date.append(groups[2])
                date.append(groups[1])
                date.append(groups[0])
                return "-".join(date)

        # month and year
        match = re.search(r"^([a-z]+).+?(-?[0-9]+)(?:\s|$)", string, re.I)
        if match:
            groups = list(match.groups())
            if groups[0].lower() in months:	
                groups[0] = str(months.index(groups[0].lower())+1)
                if 0 < int(groups[0]) < 10 and len(groups[0]) == 1:
                    groups[0] = f"0{groups[0]}"
                date.append(groups[1])
                date.append(groups[0])
                date.append("??")
                return "-".join(date)

        # year only
        match = re.search(r"^(-?[0-9]+)(?:[^,0-9]|$)", string, re.I)
        if match:
            date.append(match.group(1))
            date.append("??")
            date.append("??")
            return "-".join(date)

        # invalid date
        # TODO: log?
        return ""

    ##
    # @brief deals dates when no template was found
    # @param string - date with no template
    # @return date in YYYY-MM-DD format
    # 
    # e.g.: January 16, 1962 (extracted from the first sentence)
    #
    # date extraction helper function
    def parse_no_template(self, string):
        if re.search(r"[0-9]+/[0-9]+/[0-9]+", string):
            # invalid template
            # TODO: log?
            return ""

        string = re.sub(r"''circa''|circa|c\.|\(.*?age.*?\)|no|AD", "", string, re.I)
        string = re.sub(r"{{nbsp}}|&nbsp;", " ", string, re.I)
        string = re.sub(r"([0-9]+)(?:\/|–|-)[0-9]+", r"\1", string, re.I)
        string = re.sub(r"([0-9]+)\s+BCE?|BCE?\s+([0-9]+)", r"-\1\2", string, re.I)

        return self.parse_string_format(string.strip())

    ##
    # @brief orders dates (from oldest to newest)
    # @param array - array with up to 2 dates
    # @return ordered array of dates
    #
    # date extraction helper function
    @staticmethod
    def order_dates(array):
        reverse = True if array[0].startswith("-") and array[1].startswith("-") else False
        return sorted(array, key=lambda x: x if x != "" else "z", reverse=reverse)
