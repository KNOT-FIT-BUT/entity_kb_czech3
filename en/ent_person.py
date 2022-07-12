"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntPerson', která uchovává údaje o osobách.
Poznámka: inspirováno projektem entity_kb_czech3
"""

import re

from ent_core import EntCore

class EntPerson(EntCore):
    """
    třída určená pro osoby
    instanční atributy:
        title       - jméno osoby
        prefix      - prefix entity
        eid         - ID entity
        link        - odkaz na Wikipedii
        birth_date  - datum narození osoby
        birth_place - místo narození osoby
        death_date  - datum úmrtí osoby
        death_place - místo úmrtí osoby
        gender      - pohlaví osoby
        jobs        - zaměstnání osoby
        nationality - národnost osoby
    """
    def __init__(self, title, prefix, link, data, langmap, redirects, debugger):
        """
        inicializuje třídu EntPerson
        """
        # vyvolání inicializátoru nadřazené třídy
        super(EntPerson, self).__init__(title, prefix, link, data, langmap, redirects, debugger)

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

    def __repr__(self):
        """
        serializuje parametry třídy EntPerson
        """
        data = [
            self.gender,
            self.birth_date,
            self.birth_place,
            self.death_date,
            self.death_place,
            self.jobs,
            self.nationality
        ]
        self.d.log_message(f"stats_ent,person,{'$'.join(data)}")
        return self.serialize("\t".join(data))
    
    def assign_values(self):
        """
        pokusí se extrahovat parametry z infoboxů
        """

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
    
    def assign_dates(self):
        """
        Pokusí se extrahovat datumy úmrtí a narození z infoboxů death_date a birth_date.
        """

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

    def assign_places(self):
        """
        pokusí se extrahovat místo narození a úmrtí z infoboxů birth_place a death_place
        """       
        if "birth_place" in self.infobox_data:
            self.birth_place = self.fix_place(self.infobox_data["birth_place"])

        if "death_place" in self.infobox_data:
            self.death_place = self.fix_place(self.infobox_data["death_place"])
    
    # @staticmethod
    def fix_place(self, place):
        """
        upraví místa do vyhovujícího tvaru
        """
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
        
    def assign_nationality(self):
        """
        extrakce národnosti z infoboxu nationality
        """
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

    def assign_gender(self):
        """
        extrakce pohlaví z infoboxu gender
        """
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
    
    def assign_jobs(self):
        """
        extrakce prací z infoboxu occupation
        """
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

    def assign_urls(self):
        if "website" in self.infobox_data and self.infobox_data["website"] != "":
            value = self.infobox_data["website"]

            value = re.sub(r"\{\{url\|(?:.*?=)?([^\|\}]+).*?\}\}", r"\1", value, flags=re.I)
            value = re.sub(r"\[(.*?)\s.*?\]", r"\1", value)

            self.urls = value

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

        
