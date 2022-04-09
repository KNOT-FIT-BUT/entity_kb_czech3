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
    def __init__(self, title, prefix, link):
        """
        inicializuje třídu EntPerson
        """
        # vyvolání inicializátoru nadřazené třídy
        super(EntPerson, self).__init__(title, prefix, link)

        # inicializace údajů specifických pro entitu
        self.birth_date = ""
        self.birth_place = ""
        self.death_date = ""
        self.death_place = ""
        self.gender = ""
        self.jobs = ""
        self.nationality = ""

    def __repr__(self):
        """
        serializuje parametry třídy EntPerson
        """
        return self.serialize(f"{self.gender}\t{self.birth_date}\t{self.birth_place}\t{self.death_date}\t{self.death_place}\t{self.jobs}\t{self.nationality}")
    
    def assign_values(self):
        """
        pokusí se extrahovat parametry z infoboxů
        """
        # TODO: optimize and refactor this

        if "character" in self.infobox_name:
            self.prefix += ":fictional"

        self.assign_dates()
        self.assign_places()
        self.assign_nationality()
        self.assign_gender()
        self.assign_jobs()
        
    def assign_dates(self):
        """
        pokusí se extrahovat datumy úmrtí a narození z infoboxů death_date a birth_date
        TODO: refactor
        TODO: extrakce z první věty
        """
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        # death date extraction (death_date sometimes includes birth date, if found it is also extracted)
        if "death_date" in self.infobox_data and self.infobox_data["death_date"]:
            dates = ["", ""]
            string = self.infobox_data["death_date"]
            
            # BC and AD
            if "BC" in string:
                string = re.sub("&nbsp;|{{nbsp}}", " ", string)
                string = re.sub(r"\(.*?\)", "", string)
                string = re.sub(r"{{.*?([0-9]+).*?}}", r"\1", string)
                string = re.sub(r"{{.*}}", "", string).strip()
                string = re.sub(r"([0-9]+)/([0-9]+)", r"\1", string)
                if (string.startswith("c.")):
                    string = string[2:].strip()
                string = re.sub(r"\[\[.*\|(.*)\]\]", r"\1", string)
                string = re.sub(r"BCE|BC", "", string).strip()
                f = self.format_date(string)
                if (f != -1):
                    dates[0] = f"-{f}"
                else:
                    dates[0] = -1

            if "AD" in string:
                string = re.sub("&nbsp;|{{nbsp}}", " ", string)
                string = re.sub(r"\(.*?\)", "", string)
                string = re.sub(r"{{.*?([0-9]+).*?}}", r"\1", string)
                string = re.sub(r"{{.*}}", "", string).strip()
                string = re.sub(r"(.*?)\|.+", r"\1", string).strip()
                if (string.startswith("c.")):
                    string = string[2:].strip()
                string = string.replace(" AD", "")
                f = self.format_date(string)
                dates[0] = f
            
            # month name in date
            if dates[0] == "":
                patterns = [r"(\w+)\s+([0-9]{1,2}),?\s+([0-9]{1,4})", r"([0-9]{1,2})\s+(\w+)\s+([0-9]{1,4})"]
                pos = [[0, 1], [1, 0]]
                for j in range(len(patterns)):
                    match = re.findall(patterns[j], string)
                    if match:
                        for i in range(len(match)):
                            date = ["", "", ""]
                            date[0] = match[i][2]
                            if match[i][pos[j][0]] in months:
                                month_number = months.index(match[i][pos[j][0]])+1
                                date[1] = str(month_number) if month_number > 9 else  "0" + str(month_number)
                            date[2] = match[i][pos[j][1]] if len(match[i][pos[j][1]]) == 2 else "0"+match[i][pos[j][1]]
                            dates[i] = "-".join(date)
                            break
            
            # normal format (e.g.: ...|2000|01|01|2001|01|01... )
            if dates[0] == "":
                #YYYY|MM|DD|YYYY|MM|DD or YYYY|MM|DD
                pattern = "{{.*?([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2})\s?\|([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2}).*?}}|{{.*?([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2})[^0-9].*?"
                match = re.search(pattern, string)
                if match:
                    groups = [g for g in match.groups() if g != None]
                    for i in range(int(len(groups) / 3)):
                        month = groups[i*3+1] if len(groups[i*3+1]) == 2 else "0"+groups[i*3+1]
                        day = groups[i*3+2] if len(groups[i*3+2]) == 2 else "0"+groups[i*3+2]
                        dates[i] = "-".join([groups[i*3+0], month, day])
            
            # other formats     
            if dates[0] == "":
                string = re.sub(r"{{.*[dD]eath.*?([0-9]+).*}}", r"\1", string).strip()
                string = re.sub(r"\(.*\)|{{.*}}", "", string).strip()
                if (string.startswith("c.")):
                    string = string[2:].strip()
                f = self.format_date(string)
                if f != -1:
                    dates[0] = f

            if dates[0] != "" and dates[0] != -1:
                self.death_date = dates[0]
                self.birth_date = dates[1]
        else:
            #print(f"{self.title}: did not find a death date inside the infobox...")
            pass

        # birth date extraction
        if self.birth_date == "" and "birth_date" in self.infobox_data:
            #print(self.infobox_data['birth_date'])
            date = ""
            string = self.infobox_data["birth_date"]

            # BC and AD
            if "BC" in string:
                string = re.sub("&nbsp;|{{nbsp}}", " ", string)
                string = re.sub(r"\(.*?\)", "", string)
                string = re.sub(r"{{.*?([0-9]+).*?}}", r"\1", string)
                string = re.sub(r"{{.*}}", "", string).strip()
                string = re.sub(r"([0-9]+)/([0-9]+)", r"\1", string)
                if (string.startswith("c.")):
                    string = string[2:].strip()
                string = re.sub(r"\[\[.*\|(.*)\]\]", r"\1", string)
                string = re.sub(r"BCE|BC", "", string).strip()
                f = self.format_date(string)
                if (f != -1):
                    date = f"-{f}"
                else:
                    date = -1

            if "AD" in string:
                string = re.sub("&nbsp;|{{nbsp}}", " ", string)
                string = re.sub(r"\(.*?\)", "", string)
                string = re.sub(r"{{.*?([0-9]+).*?}}", r"\1", string)
                string = re.sub(r"{{.*}}", "", string).strip()
                string = re.sub(r"(.*?)\|.+", r"\1", string).strip()
                if (string.startswith("c.")):
                    string = string[2:].strip()
                string = string.replace(" AD", "")
                f = self.format_date(string)
                date = f
            
            # month name in date
            if date == "":
                patterns = [r"(\w+)\s+([0-9]{1,2}),?\s+([0-9]{1,4})", r"([0-9]{1,2})\s+(\w+)\s+([0-9]{1,4})"]
                pos = [[0, 1], [1, 0]]
                for j in range(len(patterns)):
                    match = re.search(patterns[j], string)
                    if match:
                        arr = ["", "", ""]
                        arr[0] = match.group(3)
                        if match.group(pos[j][0]+1) in months:
                            month_number = months.index(match.group(pos[j][0]+1))+1
                            arr[1] = str(month_number) if month_number > 9 else  "0" + str(month_number)
                        arr[2] = match.group(pos[j][1]+1) if len(match.group(pos[j][1]+1)) == 2 else "0"+match.group(pos[j][1]+1)
                        date = "-".join(arr)
            
            # normal date format
            if date == "":
                #YYYY|MM|DD|YYYY|MM|DD or YYYY|MM|DD
                pattern = "{{.*?([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2}).*?}}"
                match = re.search(pattern, string)
                if match:
                    groups = [g for g in match.groups() if g != None]
                    for i in range(int(len(groups) / 3)):
                        month = groups[i*3+1] if len(groups[i*3+1]) == 2 else "0"+groups[i*3+1]
                        day = groups[i*3+2] if len(groups[i*3+2]) == 2 else "0"+groups[i*3+2]
                        date = "-".join([groups[i*3+0], month, day])

            # other formats     
            if date == "":
                string = re.sub(r"{{.*[dD]eath.*?([0-9]+).*}}", r"\1", string).strip()
                string = re.sub(r"\(.*\)|{{.*}}", "", string).strip()
                if (string.startswith("c.")):
                    string = string[2:].strip()
                f = self.format_date(string)
                if f != -1:
                    date = f

            if date != "" and date != -1:
                self.birth_date = date            
        else:
            #print(f"{self.title}: did not find a birth date inside the infobox...")
            pass

    @staticmethod
    def format_date(string):
        """
        upraví datumy do vyhovujícího tvaru
        """
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        # month in the middle (DD month YYYY)
        m = re.search(r"([0-9]+)\s(\w+)\s([0-9]+)", string)
        if m:
            month = ""
            day = int(m.group(1))
            if m.group(2) in months:
                month = months.index(m.group(2))+1 
                month = str(month) if month > 9 else f"0{month}"
            else:
                return -1
            day = str(day) if day > 9 else f"0{day}"
            return f"{m.group(3)}-{month}-{day}"
            
        # month first (month DD YYYY)
        m = re.search(r"(\w+)\s([0-9]+)\s([0-9]+)", string)
        if m:
            month = ""
            day = int(m.group(2))
            if m.group(1) in months:
                month = months.index(m.group(1))+1 
                month = str(month) if month > 9 else f"0{month}"
            else:
                return "date format error"
            day = str(day) if day > 9 else f"0{day}"
            return f"{m.group(3)}-{month}-{day}"
        
        # month and year (month YYYY)
        m = re.search(r"(\w+)\s([0-9]+)", string)
        if m:
            month = ""
            if m.group(1) in months:
                month = months.index(m.group(1))+1 
                month = str(month) if month > 9 else f"0{month}"
            else:
                return -1
            return f"{m.group(2)}-{month}-??"
        
        if (re.search(r"[^0-9]+", string) or string == ""):
            return -1
        
        # year only (YYYY)
        return f"{string}-??-??"

    def assign_places(self):
        """
        pokusí se extrahovat místo narození a úmrtí z infoboxů birth_place a death_place
        """       
        if "birth_place" in self.infobox_data:
            self.birth_place = self.fix_place(self.infobox_data["birth_place"])

        if "death_place" in self.infobox_data:
            self.death_place = self.fix_place(self.infobox_data["death_place"])
    
    @staticmethod
    def fix_place(place):
        """
        upraví místa do vyhovujícího tvaru
        """
        p = place

        if p == "":
            return p

        if p[0:9].lower() == "{{nowrap|":
            p = p[9:-2]
        
        if p.startswith("{{"):
            return ""
        else:
            p = re.sub(r"\[|\]|'", "", p)
            p = re.sub(r"\|", ", ", p)
        return p
        
    def assign_nationality(self):
        """
        extrakce národnosti z infoboxu nationality
        TODO: extrakce z první věty
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
                nationalities[i] = bar_split[-1].strip()
                
            self.nationality = " | ".join(nationalities)

    def assign_gender(self):
        """
        extrakce pohlaví z infoboxu gender
        TODO (TEST): extrakce z druhé věty
        """
        if "gender" in self.infobox_data and self.infobox_data["gender"] != "":
            gender = self.infobox_data["gender"].lower()
            self.gender = gender

        # TODO: move this out of infobox extraction 
        if self.gender == "":
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
        TODO (WIP): extrakce z první věty          
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
                        tmp.append(s)
            
            occupation = tmp
            
            self.jobs = " | ".join(occupation)

        # first_sentence = self.first_paragraph        
        # # match the firsst sentence
        # match = re.search(r"(?:[a-z]|\])\.(?:\s|\n)", first_sentence)
        # if match:
        #     first_sentence = first_sentence[:match.span()[0]+2]
        
        # match = re.search(r"(?:\bwas\b|\bis\b)\s(?:\ban\b|\ba|b)\s(.*)\.", first_sentence)
        # if match:
        #     if match.group(1):
        #         first_sentence = match.group(1)
        #     else:
        #         return
        # else:
        #     return
        
        # # get rid of ... was a {data} who ...
        # # get the second word
        # match = re.search(r"\[\[([^\[]*\|).*?]]", first_sentence)
        # if match:
        #     for item in match.groups():
        #         first_sentence = first_sentence.replace(item, "")
        # first_sentence = re.sub(r"\[|\]", "", first_sentence)
        
        # first_lowercase = first_sentence.split()
        # for i in range(len(first_lowercase)):
        #     match = re.search(r"^[a-z]", first_lowercase[i])
        #     if match:
        #         first_sentence = " ".join(first_lowercase[i:])
        #         break
            
        # first_sentence = first_sentence.strip()
        # split = first_sentence.split(",")
        # for s in split:
        #     if len(s)>40:
        #         print(f"{self.title}: unidentifiable")
        #         return
        # last = split.pop()
        # last_split = last.split("and", 1)
        # for s in last_split:
        #     if s != " ":
        #         split.append(s.strip())
        # print(f"{self.title}: {split}")
        pass

    @staticmethod
    def is_person(content):
        """
        na základě obsahu stránky určuje, zda stránka pojednává o osobě, či nikoliv
        parametry:
        content - obsah stránky
        návratové hodnoty: True / False
        """

        # TODO: další možné problematické skupiny, které zatím nejsou řešeny
        # transgender

        # birth or births
        if (re.search(r"\[\[Category:.*?\bbirths?\b.*?\]\]", content, re.I)):
            return True
        # death or deaths
        if (re.search(r"\[\[Category:.*?\bdeaths?\b.*?\]\]", content, re.I)):
            return True
        # men or women
        if (re.search(r"\[\[Category:.*?\b(wo)?men\b.*?\]\]", content, re.I)):
            return True
        # characters
        if (re.search(r"\[\[Category:.*?\bcharacters\b.*?\]\]", content, re.I)):
            return True

        return False

        
