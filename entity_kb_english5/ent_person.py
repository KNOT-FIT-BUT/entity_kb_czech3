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
        
        # TODO: optimize this
        self.assign_dates()
        self.assign_places()
        self.assign_nationality()
        self.assign_gender()
        #self.assign_jobs()
        

    def assign_dates(self):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        # search infobox
        if "birth_date" in self.infobox_data:
            #print(self.infobox_data['birth_date'])
            # looks for YYYY|MM|DD
            # TODO: this is matching {{birth-date|20 August 1898}}
            pattern = r"^{{.*([0-9]{4})\|?([0-9]{1,2})?\|?([0-9]{1,2})?"
            match = re.search(pattern, self.infobox_data["birth_date"])
            if match:
                # YYYY-MM-DD
                groups = list(match.groups())
                # if day or month is missing filter None values
                def group_filter(group):
                    return False if group == None else True
                groups = list(filter(group_filter, groups))
                self.birth_date = "-".join(groups)        
            else:
                pattern = r"(\w+\s\d{1,2}.*?\d{1,4})|(\d{1,2}?\s?\w+\s\d{1,4})"
                match = re.search(pattern, self.infobox_data["birth_date"])
                if match:
                    #print(f"{match.group(1)} - {match.group(2)}\t{self.title}")
                    if match.group(1):
                        split = match.group(1).split()
                        month = months.index(split.pop(0)) + 1
                        day = -1
                        if len(split) == 2:
                            day = split.pop(0)[0:-1]
                        year = split[0]
                        self.birth_date = f"{year}-{month}-{day}" if day != -1 else f"{year}-{month}"
                    elif match.group(2):
                        split = match.group(2).split()
                        self.birth_date = f"{split[2]}-{months.index(split[1])+1}-{split[0]}"
                    else:
                        print("no match")
        else:
            #print(f"{self.title}: did not find a birth date inside the infobox...")
            pass
        
        if "death_date" in self.infobox_data:
            # matches format {{.*YYYY|MM|DD|YYYY|MM|DD.*}}
            pattern = r"^{{.*?([0-9]{1,4})\|([0-9]{1,2})\|([0-9]{1,2})\|([0-9]{1,4})\|?([0-9]{1,2})\|([0-9]{1,2}).*}}$"
            match = re.search(pattern, self.infobox_data["death_date"])
            if match and len(match.groups()) == 6:
                death_groups = list(match.groups())[0:3]
                self.death_date = "-".join(death_groups)
                birth_groups = list(match.groups())[3:6]
                if self.birth_date != "-".join(birth_groups):
                    #print(f"{self.title}: updating birth_date from death_date")
                    self.birth_date = "/".join(birth_groups)
            else:
                if self.infobox_data["death_date"] == "":
                    self.death_date = "alive"
                else:
                    self.death_date = "no match or bad match"              
        else:
            #print(f"{self.title}: did not find a death date inside the infobox...")
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
        if "nationality" in self.infobox_data:
            if self.infobox_data["nationality"]:
                nationality = self.infobox_data["nationality"]
                nationality = re.sub("\[|\]", "", nationality)
                # TODO: is this optimal? i think not
                if nationality.startswith("{{hlist"):
                    nationality = nationality[10:-2]
                self.nationality = nationality
                print(nationality)

    def assign_gender(self):
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
        first_sentence = self.first_paragraph        
        # match the firsst sentence
        match = re.search(r"(?:[a-z]|\])\.(?:\s|\n)", first_sentence)
        if match:
            first_sentence = first_sentence[:match.span()[0]+2]
        
        match = re.search(r"(?:\bwas\b|\bis\b)\s(?:\ban\b|\ba|b)\s(.*)\.", first_sentence)
        if match:
            if match.group(1):
                first_sentence = match.group(1)
            else:
                return
        else:
            return
        
        # get rid of ... was a {data} who ...
        # get the second word
        match = re.search(r"\[\[([^\[]*\|).*?]]", first_sentence)
        if match:
            for item in match.groups():
                first_sentence = first_sentence.replace(item, "")
        first_sentence = re.sub(r"\[|\]", "", first_sentence)
        
        first_lowercase = first_sentence.split()
        for i in range(len(first_lowercase)):
            match = re.search(r"^[a-z]", first_lowercase[i])
            if match:
                first_sentence = " ".join(first_lowercase[i:])
                break
            
        first_sentence = first_sentence.strip()
        split = first_sentence.split(",")
        for s in split:
            if len(s)>40:
                print(f"{self.title}: unidentifiable")
                return
        last = split.pop()
        last_split = last.split("and", 1)
        for s in last_split:
            if s != " ":
                split.append(s.strip())
        print(f"{self.title}: {split}")

    def serialize(self):
        return f"{self.prefix}\t{self.title}\t{self.birth_date}\t{self.birth_place}\t{self.death_date}\t{self.death_place}\t{self.gender}\t{self.nationality}\t{self.link}"

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
