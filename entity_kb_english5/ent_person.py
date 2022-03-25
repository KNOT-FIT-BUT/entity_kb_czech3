"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntPerson', která uchovává údaje o lidech.
Poznámka: inspirováno projektem entity_kb_czech3
"""

import re

from ent_core import EntCore

class EntPerson(EntCore):
    """
    Třída určená pro lidi.
    Instanční atributy:
    title       - jméno osoby (str)
    prefix      - prefix entity (str)
    eid         - ID entity (str)
    link        - odkaz na Wikipedii (str)
    aliases     - alternativní jména osoby (str)
    description - stručný popis osoby (str)
    images      - absolutní cesty k obrázkům Wikimedia Commons (str)
    birth_date  - datum narození osoby (str)
    birth_place - místo narození osoby (str)
    death_date  - datum úmrtí osoby (str)
    death_place - místo úmrtí osoby (str)
    gender      - pohlaví osoby (str)
    jobs        - zaměstnání osoby (str)
    nationality - národnost osoby (str)
    Třídní atributy:
    ib_types    - typy infoboxů, které se týkají osob (set)
    TODO
    """
    def __init__(self, title, prefix, link):
        """
        Inicializuje třídu 'EntPerson'.
        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        TODO
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
    
    def assign_values(self):
        
        # TODO: optimize and refactor this
        self.assign_dates()
        self.assign_places()
        self.assign_nationality()
        self.assign_gender()
        self.assign_jobs()
        

    def assign_dates(self):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        
        if "death_date" in self.infobox_data:
            dates = ["", ""]
            string = self.infobox_data["death_date"]
            
            # bc in date
            if "BC" in string:
                string = string.replace("&nbsp;", " ")
                dates[0] = string
            
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
            
            # normal format
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

            if dates[0] == "":
                #print(f"{self.title}: {self.infobox_data['death_date']}")
                pass

            self.death_date = dates[0]
            self.birth_date = dates[1]
        else:
            #print(f"{self.title}: did not find a death date inside the infobox...")
            pass

        # search infobox
        if self.birth_date == "" and "birth_date" in self.infobox_data:
            #print(self.infobox_data['birth_date'])
            date = ""
            string = self.infobox_data["birth_date"]

            if "BC" in string:
                string = string.replace("&nbsp;", " ")
                date = string
            
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

            if date == "":
                #print(f"{self.title}: {self.infobox_data['birth_date']}")
                pass

            self.birth_date = date            
        else:
            #print(f"{self.title}: did not find a birth date inside the infobox...")
            pass

    def assign_places(self):
        # birth_place        
        if "birth_place" in self.infobox_data:
            self.birth_place = self._fix_place(self.infobox_data["birth_place"])

        if "death_place" in self.infobox_data:
            self.death_place = self._fix_place(self.infobox_data["death_place"])
    
    @staticmethod
    def _fix_place(place):
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
        if "nationality" in self.infobox_data and self.infobox_data["nationality"] != "":
            nationalities = []
            string = self.infobox_data["nationality"]
            string = re.sub(r"\(.*\)|\[|\]", "", string).strip()
            
            # case splitting
            indexes = [m.start(0) for m in re.finditer(r"[a-z][A-Z]", string)]
            x = 0
            for i in indexes:
                nationalities.append(string[x:i+1])
                x = i+1
            nationalities.append(string[x:])
            
            # other splitting
            splitters = ["/", "-", "–", ","]
            for splitter in splitters:
                tmp = []
                for s in nationalities:
                    for a in s.split(splitter):
                        tmp.append(a)
                
                nationalities = tmp
            
            for i in range(len(nationalities)):
                bar_split = nationalities[i].split("|")
                nationalities[i] = bar_split[-1].strip()
                
            self.nationality = " | ".join(nationalities)

    def assign_gender(self):
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
    
    # TODO: WIP
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

    def serialize(self):
        return f"{self.prefix}\t{self.title}\t{self.gender}\t{self.birth_date}\t{self.birth_place}\t{self.death_date}\t{self.death_place}\t{self.jobs}\t{self.nationality}\t{self.link}"

    # TODO: classmethod?
    @classmethod
    def is_person(cls, content):
        """
        Na základě obsahu stránky určuje, zda stránka pojednává o osobě, či nikoliv.
        Parametry:
        content - obsah stránky (str)
        Návratové hodnoty:
        TODO
        """

        # TODO: person categories
        score = cls._check_categories(content)

        # TODO: more checks if necessery

        # TODO: change number?
        if score >= 1:
            #print("DEBUG: identified person " + str(score))
            return True
        else:
            #print("DEBUG: did not identify person")
            return False        

    @staticmethod
    def _check_categories(content):
        """
        Kontroluje, zda obsah stránky obsahuje některou z kategorií, které identifikují stránky o osobách.
        Parametry:
        content - obsah stránky (str)
        Návratové hodnoty:
        TODO: Pravděpodobnost, že je stránka o osobě. (int)
        """
        # TODO
        score = 0

        #paragraphs = content.split("\n\n")        
        #print(paragraphs[-1])

        # TODO: další možné problematické skupiny, které zatím nejsou řešeny
        # gods and heroes (mythology)
        # transgender
        # book characters

        # "birth or births" in categories
        if (re.search(r"\[\[Category:.*?\bbirths?\b\]\]", content, re.I)):
            score += 1
        # "death or deaths" in categories
        if (re.search(r"\[\[Category:.*?\bdeaths?\b\]\]", content, re.I)):
            score += 1
        # "men or women" in categories
        if (re.search(r"\[\[Category:.*?\b(wo)?men\b.*?\]\]", content, re.I)):
            score += 1
        # "people" in categories
        if (re.search(r"\[\[Category:.*?\bpeople\b.*?\]\]", content, re.I)):
            score += 1
        return score
