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
    def __init__(self, title, prefix, link, langmap, redirects):
        """
        inicializuje třídu EntPerson
        """
        # vyvolání inicializátoru nadřazené třídy
        super(EntPerson, self).__init__(title, prefix, link, langmap, redirects)

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

    @staticmethod
    def format_death_date(string):
        string = re.sub(r" \|", "|", string)
        bad = False
        data = string.split("|")
        data = [d for d in data[1:] if "=" not in d and d != ""]
        for d in data:
            if re.search(r"[^0-9]", d):
                bad = True
        if bad:
            death = EntPerson.format_other_date(data[0])
            birth = EntPerson.format_other_date(data[1])
            return (birth, death)
        
        for i in range(len(data)):
            data[i] = f"0{int(data[i])}" if int(data[i]) < 10 else data[i]
        #print(f"birth {'-'.join(data[3:])}\tdeath {'-'.join(data[:3])}")
        return ('-'.join(data[3:]), '-'.join(data[:3]))

    @staticmethod
    def format_birth_date(string):
        string = re.sub(r"year=|month=|day=", "", string)
        data = string.split("|")
        data = [d.strip() for d in data[1:] if "=" not in d and d != ""]
        for d in data:
            if re.search(r"[^0-9]", d):                
                return EntPerson.format_other_date(d)
        for i in range(len(data)):
            data[i] = f"0{int(data[i])}" if int(data[i]) < 10 else data[i]
        
        #print("-".join(data) + "\t" + self.title)
        return "-".join(data)
    
    @staticmethod
    def format_other_date(string):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        # either BC or AD in string
        if "BC" in string or "BCE" in string or "AD" in string:
            string = re.sub(r" AD", "", string)
            string = re.sub(r"([0-9]+) BCE?", r"-\1", string)

        # or
        # August 16, 1946
        # 31 July 2004
        m = re.search(r"(\w+)\s([0-9]+),?\s(-?[0-9]+)", string)
        if m:
            data = []
            if m.group(1) not in months:
                return
            data.append(months.index(m.group(1)) + 1)
            data.append(m.group(2))
            for i in range(len(data)):
                data[i] = f"0{int(data[i])}" if int(data[i]) < 10 else str(data[i])
            #print(f"{date} {m.group(3)}-{data[0]}-{data[1]}")
            return f"{m.group(3)}-{data[0]}-{data[1]}"
        m = re.search(r"([0-9]+)\s(\w+)\s(-?[0-9]+)", string)
        if m:
            data = []
            if m.group(2) not in months:
                return
            data.append(months.index(m.group(2)) + 1)
            data.append(m.group(1))
            for i in range(len(data)):
                data[i] = f"0{int(data[i])}" if int(data[i]) < 10 else str(data[i])
            #print(f"{date} {m.group(3)}-{data[0]}-{data[1]}")
            return f"{m.group(3)}-{data[0]}-{data[1]}"

        # or
        # June 218
        m = re.search(r"^(\w+)\s(-?[0-9]+)$", string)
        if m:
            if m.group(1) not in months:
                return
            month = months.index(m.group(1)) + 1
            #print(f"{date} {m.group(2)}-{month}-??")
            return f"{m.group(2)}-{month}-??"

        # or
        # 1948
        if re.search(r"^-?[0-9]+$", string):
            #print(f"{date} {string}-??-??")
            return f"{string}-??-??"

        # or invalid
        # print("error")
        return ""

    def assign_dates(self):
        """
        pokusí se extrahovat datumy úmrtí a narození z infoboxů death_date a birth_date
        TODO: extrakce z první věty
        """

        keys = ("death_date", "birth_date")
        for key in keys:
            if key in self.infobox_data and self.infobox_data[key] != "":
                date = self.infobox_data[key].strip()

                # death date and age
                pattern = r"{{((?:[Dd]eath(?:\s|-)date and age|dda|[Dd]-da).*?)}}"           
                m = re.search(pattern, date)
                if m:
                    self.birth_date, self.death_date = self.format_death_date(m.group(1))
                    return

                # death year and age
                pattern = r"{{(?:[Dd]eath year and age|death year)\s?\|([0-9]+)\|([0-9]+).*?}}"
                m = re.search(pattern, date)
                if m:
                    #print(f"birth {m.group(2)}-??-??\tdeath {m.group(1)}-??-??")
                    self.birth_date = f"{m.group(2)}-??-??"
                    self.death_date = f"{m.group(1)}-??-??"
                    return

                # death date
                pattern = r"{{[Dd]eath date.*?\|([0-9]+)\|([0-9]+)\|([0-9]+).*?}}"
                m = re.search(pattern, date)
                if m:
                    groups = []
                    for group in m.groups():
                        groups.append(f"0{int(group)}" if int(group) < 10 else group)
                    #print(f"death {groups[0]}-{groups[1]}-{groups[2]}")
                    self.death_date = f"{groups[0]}-{groups[1]}-{groups[2]}"
                    continue

                # birth date and age | birth date
                pattern = r"{{((?:[Bb]irth(?:\s|-)date and age|[Bb]irth date|b-da).*?)}}"
                m = re.search(pattern, date)
                if m:
                    self.birth_date = self.format_birth_date(m.group(1))
                    return

                # birth year and age
                pattern = r"{{(?:[Bb]irth year and age|birth year)\s?\|([0-9]+).*?}}"
                m = re.search(pattern, date)
                if m:
                    #print(f"birth {m.group(1)}-??-??")
                    self.birth_date = f"{m.group(1)}-??-??"
                    return

                date = re.sub(r"{{(?:[Bb]irth-date|[Dd]eath-date)\|(.*?)}}", r"\1", date)
                date = re.sub(r"\(.*?\)|'", "", date)
                date = re.sub(r".*/.*/.*", "", date)
                date = re.sub(r"&nbsp;|{{nbsp}}", " ", date)
                date = re.sub(r"{{(?:circa|nowrap)\|(.*?)(?:\|.*?)?}}", r"\1", date)
                date = re.sub(r"{{c\..*?\|([0-9]+).*?}}", r"\1", date)
                date = re.sub(r"circa", "", date)
                date = re.sub(r"c\.\s", "", date)
                date = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", date)
                date = re.sub(r"{{.*?}}", "", date)
                date = re.sub(r".*?([0-9]+)/[0-9]+.*", r"\1", date)

                date = date.strip()

                if date != "":
                    if key == "death_date":
                        self.death_date = self.format_other_date(date)
                        continue
                    else:
                        self.birth_date = self.format_other_date(date)
                        return

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
                bar_split[-1] = re.sub(r"{|}", "", bar_split[-1]).strip()
                nationalities[i] = bar_split[-1]
            
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
            
            self.jobs = "|".join(occupation)

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

        
