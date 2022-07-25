##
# @file ent_person.py
# @brief contains EntPerson class - entity used for people, artists and groups
#
# @section ent_information entity information
# person and person:fictional:
# - birth_date
# - birth_place
# - death_date
# - death_place 
# - gender
# - jobs
# - nationality
#
# person:artist
# - art_forms
# - urls
#
# person:group - same as person but the values are arrays separated by |
#
# @todo finish artist
# @todo add group extraction
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from entities.ent_core import EntCore

##
# @class EntPerson
# @brief entity used for people, artists and groups
class EntPerson(EntCore):
    ##
    # @brief initializes the person entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
    def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
        # vyvolání inicializátoru nadřazené třídy
        super(EntPerson, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

        # inicializace údajů specifických pro entitu
        self.birth_date = ""
        self.birth_place = ""
        self.death_date = ""
        self.death_place = ""
        self.gender = ""
        self.jobs = ""
        self.nationality = ""
        
        # artist
        self.art_forms = ""
        self.urls = ""

    ##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
    def __repr__(self):
        data = [
            self.gender,
            self.birth_date,
            self.birth_place,
            self.death_date,
            self.death_place,
            self.jobs,
            self.nationality
        ]
        return self.serialize("\t".join(data))
    
    ##
    # @brief tries to assign entity information (calls the appropriate functions)
    def assign_values(self):
        self.assign_prefix()
        
        # if self.prefix != "person:fictional":
        #     self.d.log_categories(self.categories)

        self.assign_dates()
        self.assign_places()
        self.assign_nationality()
        self.assign_gender()
        self.assign_jobs()        

        if self.prefix == "person:artist":
            self.assign_art_forms()
            self.assign_urls()
    
    ##
    # @brief extracts and assigns dates from infobox or from the first sentence
    def assign_dates(self):
        if "birth_date" in self.infobox_data and self.infobox_data["birth_date"] != "":
            date = self.infobox_data["birth_date"].strip()
            extracted = self.extract_date(date)
            self.birth_date = extracted[0]
        
        if "death_date" in self.infobox_data and self.infobox_data["death_date"] != "":
            date = self.infobox_data["death_date"].strip()
            extracted = self.extract_date(date)
            if extracted[1] == "":
                self.death_date = extracted[0]
            else:
                if self.birth_date == "":
                    self.birth_date = extracted[0]
                self.death_date = extracted[1]

        # try to get the date from the 1st sentence
        if (self.death_date == "" or self.birth_date == "") and self.prefix != "person:fictional":        
            match = re.search(r"\((.*?)\)", self.first_paragraph)
            if match:
                group = match.group(1)
                group = re.sub(r"\[\[.*?\]\]", "", group)
                group = re.sub(r"\{\{.*?\}\};?", "", group)
                group = re.sub(r"&ndash;", "–", group).strip()
                group = group.split("–")
                if len(group) == 2:
                    # get rid of born and died
                    born = group[0].replace("born", "").strip()
                    died = group[1].replace("died", "").strip()
                    if "BC" in died and "BC" not in born:
                        born += " BC"
                    self.birth_date = self.extract_date(born)[0]
                    self.death_date = self.extract_date(died)[0]
                else:
                    date = group[0]
                    # look for born and died
                    if "born" in date:
                        date = date.replace("born", "").strip()
                        self.birth_date = self.extract_date(date)[0]
                    elif "died" in date:
                        date = date.replace("died", "").strip()
                        self.death_date = self.extract_date(date)[0]
                    else:
                        self.birth_date = self.extract_date(date)[0]

    ##
    # @brief extracts and assigns places from infobox, removes wikipedia formatting
    def assign_places(self):   
        if "birth_place" in self.infobox_data:
            self.birth_place = self.fix_place(self.infobox_data["birth_place"])

        if "death_place" in self.infobox_data:
            self.death_place = self.fix_place(self.infobox_data["death_place"])
    
    ##
    # @brief removes wikiepdia formatting from places
    # @param place - wikipedia formatted string
    # @return string result without formatting
    def fix_place(self, place):
        p = place

        if p == "":
            return p

        p = re.sub(r"{{nowrap\|(.*?)}}", r"\1", p)
        
        if p.startswith("{{"):
            # self.d.log_message(f"couldn't fix place: {place} [{self.link}]")
            return ""
        else:
            p = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", p)
            p = re.sub(r"\[|\]", "", p)
        return p
    
    ##
    # @brief extracts and assigns nationality from infobox, removes wikipedia formatting
    def assign_nationality(self):
        if "nationality" in self.infobox_data and self.infobox_data["nationality"] != "":
            nationalities = []
            string = self.infobox_data["nationality"]

            # removing stuff in () and [] brackets 
            # (e.g.: [[Belgium|Belgian]] (1949—2003), [[Chile]]an[[Mexico|Mexican]])
            string = re.sub(r"\(.*\)|\[|\]", "", string).strip()
            
            # case splitting 
            # (e.g.: GermanAmerican)
            indexes = [m.start(0) for m in re.finditer(r"[a-z][A-Z]", string)]
            x = 0
            for i in indexes:
                nationalities.append(string[x:i+1])
                x = i+1
            nationalities.append(string[x:])
            
            # other splitting 
            # (e.g.: French-Moroccan)
            splitters = ["/", "-", "–", ","]
            for splitter in splitters:
                tmp = []
                for s in nationalities:
                    for a in s.split(splitter):
                        tmp.append(a)
                
                nationalities = tmp
            
            # splitting redirects 
            # (e.g.: [[Germans|German]]) -> German
            for i in range(len(nationalities)):
                bar_split = nationalities[i].split("|")
                bar_split[-1] = re.sub(r"{|}", "", bar_split[-1]).strip()
                nationalities[i] = bar_split[-1]
            
            self.nationality = " | ".join(nationalities)

    ##
    # @brief extracts and assigns gender from infobox and the first paragraph
    def assign_gender(self):
        if "gender" in self.infobox_data and self.infobox_data["gender"] != "":
            gender = self.infobox_data["gender"].lower()
            self.gender = gender
            return

        # extracting from categories
        # e.g.: two and a half men -> can't extract gender from this
        if self.prefix != "person:fictional":
            for c in self.categories:
                if "women" in c.lower() or "female" in c.lower():
                    self.gender = "female"
                    return
                if "male" in c.lower():
                    self.gender = "male"
                    return

        # if there is he/his/she/her in the second sentence
        # TODO: split lines better
        paragraph_split = self.first_paragraph.split(".")
        if len(paragraph_split) > 1:
            #print(f"{self.title}: {paragraph_split[1].strip()}")
            match = re.search(r"\b[Hh]e\b|\b[Hh]is\b", paragraph_split[1].strip())
            if match:
                self.gender = "male"
                return
            match = re.search(r"\b[Ss]he\b|\b[Hh]er\b", paragraph_split[1].strip())
            if match:
            # else:
            #     print(f"{self.title}: undefined")
                self.gender = "female"
    
    ##
    # @brief extracts and assigns jobs from infobox
    def assign_jobs(self):
        if "occupation" in self.infobox_data and self.infobox_data["occupation"] != "":
            string = self.infobox_data["occupation"]
            string = re.sub("\[|\]|\{|\}", "", string)
            occupation = [s.lower().strip() for s in string.split(",")]

            for i in range(len(occupation)):
                bar_split = occupation[i].split("|")
                occupation[i] = bar_split[-1]

            tmp = []
            for o in occupation:
                star_split = o.split("*")
                for s in star_split:
                    if s != "":
                        tmp.append(s.strip())
            
            occupation = tmp
            
            self.jobs = "|".join(occupation).replace("\n", " ")

    ##
    # @brief extracts and assigns art forms from infobox
    def assign_art_forms(self):
        
        keys = ["movement", "field"]

        for key in keys:
            if key in self.infobox_data and self.infobox_data[key] != "":
                value = self.infobox_data[key].replace("\n", " ")
                if "''" in value:
                    continue
                value = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", value)
                value = re.sub(r"\[|\]", "", value)
                value = re.sub(r"\{\{.*?\}\}", "", value)
                value = value.lower()
              
                value = [item.strip() for item in value.split(",")]
                
                if len(value) == 1:
                    value = value[0]
                    value = [item.strip() for item in value.split("/")]
                
                value = "|".join(value)

                if value != "":
                    if self.art_forms == "":
                        self.art_forms = value
                    else:
                        self.art_forms += f"|{value}"

    ##
    # @brief extracts and assigns urls from infobox
    def assign_urls(self):
        if "website" in self.infobox_data and self.infobox_data["website"] != "":
            value = self.infobox_data["website"]

            value = re.sub(r"\{\{url\|(?:.*?=)?([^\|\}]+).*?\}\}", r"\1", value, flags=re.I)
            value = re.sub(r"\[(.*?)\s.*?\]", r"\1", value)

            self.urls = value

    ##
    # @brief assigns prefix based on entity categories or infobox names
    #
    # person, person:fictional, person:artist or person:group
    def assign_prefix(self):
        
        if "character" in self.infobox_name or "fictional" in self.first_sentence:
            self.prefix += ":fictional"
            return

        for c in self.categories:
            if "fictional" in c.lower():
                self.prefix += ":fictional"
                return

        if self.infobox_name.lower() == "artist":
            self.prefix += ":artist"
            return

        # artist, painter, writer

        for c in self.categories:
            if re.search(r"artist", c, re.I):
                self.prefix += ":artist"
                return

        
