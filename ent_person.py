#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje třídu 'EntPerson', která uchovává údaje o lidech.
"""

import re
import regex
from ent_core import EntCore
from libs.natToKB import *


class EntPerson(EntCore):
    """
    Třída určená pro lidi.

    Instanční atributy:
    title - jméno osoby (str)
    prefix - prefix entity (str)
    eid - ID entity (str)
    link - odkaz na Wikipedii (str)
    aliases - alternativní jména osoby (str)
    description - stručný popis osoby (str)
    images - absolutní cesty k obrázkům Wikimedia Commons (str)

    birth_date - datum narození osoby (str)
    birth_place - místo narození osoby (str)
    death_date - datum úmrtí osoby (str)
    death_place - místo úmrtí osoby (str)
    gender - pohlaví osoby (str)
    jobs - zaměstnání osoby (str)
    nationality - národnost osoby (str)

    Třídní atributy:
    ib_types - typy infoboxů, které se týkají osob (set)
    """

    NT_PSEUDO = 'pseudo'
    NT_NICK = 'nick'

    # získání typů infoboxů týkajících se osob
    with open("person_infoboxes", "r", encoding="utf-8") as fl:
        ib_types = {x.lower().strip() for x in fl.readlines()}

    def __init__(self, title, prefix, link, redirects):
        """
        Inicializuje třídu 'EntPerson'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        # vyvolání inicializátoru nadřazené třídy
        super(EntPerson, self).__init__(title, prefix, link, redirects)

        # inicializace údajů specifických pro entitu
        self.birth_date = ""
        self.birth_place = ""
        self.death_date = ""
        self.death_place = ""
        self.gender = ""
        self.jobs = ""
        self.nationality = ""

    @classmethod
    def is_person(cls, content):
        """
        Na základě obsahu stránky určuje, zda stránka pojednává o osobě, či nikoliv.

        Parametry:
        content - obsah stránky (str)

        Návratové hodnoty:
        2 a více v případě, že stránka pojednává o osobě, jinak 0 nebo 1. (int)
        """
        # kontrola kategorií
        id_level = cls._contains_person_categories(content)

        # kontrola šablon
        if id_level < 2:
            tmp_infobox_substitute = re.search(r"{{substovaný\s+infobox}}", content, re.I) # https://cs.wikipedia.org/wiki/Olymp_(Manhattan) => firstly substitute infobox with location, than infobox with person => avoid to mark as person instead of location
            rexp = re.search(r"{{\s*Infobox[\-–—−\s]+(\w[\w\s]+)", content, re.I)
            if (not tmp_infobox_substitute or tmp_infobox_substitute.start() > rexp.start()) and rexp and rexp.group(1):
                ib_type = str(rexp.group(1)).lower().strip()
                if ib_type in cls.ib_types:
                    if "osoba" in ib_type:
                        id_level = 2
                    else:
                        if "hudební umělec" in ib_type:
                            if re.search(r"(?:datum|místo)[\s_](?:narození|úmrtí)\s*=(?!=)", content, re.I):
                                id_level += 1
                        else:
                            id_level += 1
                            if re.search(r"(?:datum|místo)[\s_](?:narození|úmrtí)\s*=(?!=)", content, re.I):
                                id_level += 1

        # kontrola první věty článku
        if id_level < 2:
            if re.search(r".*?'''.*?'''.*?\((?:.{0,10}[*†].*?|.*?[\-–—−].*?)\).*?\s(?:byl[aiy]?|je|jsou|patř(?:í|il)|stal)", content):
                id_level += 1

        return id_level

    @staticmethod
    def _contains_person_categories(content):
        """
        Kontroluje, zda obsah stránky obsahuje některou z kategorií, které identifikují stránky o osobách.

        Parametry:
        content - obsah stránky (str)

        Návratové hodnoty:
        Pravděpodobnost, že je stránka o osobě. (int)
        """
        id_level = 0

        # Narození 1990, Narození 3. května, Narození v Olomouci, Narození ve Slovinsku, Narození na Slovensku
        if re.search(r"\[\[\s*Kategorie:\s*Narození\s+\w", content, re.I):
            id_level += 1

        # Úmrtí 1990, Úmrtí 3. května, Úmrtí v Olomouci, Úmrtí ve Slovinsku, Úmrtí na Slovensku => Úmrtí číslo nebo Úmrtí v/ve/na <velké písmeno - pozor i Unicode velká!>
        elif regex.search(r"\[\[\s*Kategorie:\s*Úmrtí\s+(?:[0-9]|(?:ve?|na)\s+\p{Lu})", content, regex.I):
            id_level += 1

        # kategorie pro muže přímo určená ke strojovému zpracování
        if re.search(r"\[\[\s*Kategorie:\s*Muži(?:\|[^]]*)?\]\]", content, re.I):
            id_level = 2

        # kategorie pro ženy přímo určená ke strojovému zpracování
        elif re.search(r"\[\[\s*Kategorie:\s*Ženy(?:\|[^]]*)?\]\]", content, re.I):
            id_level = 2

        # kategorie pro transsexuály přímo určená ke strojovému zpracování
        elif re.search(r"\[\[\s*Kategorie:\s*Transsexuálové(?:\|[^]]*)?\]\]", content, re.I):
            id_level = 2

        # kategorie určená (možná) žijícím lidem
        elif re.search(r"\[\[\s*Kategorie:\s*(?:Možná\s+)?žijící\s+lidé(?:\|[^]]*)?\]\]", content, re.I):
            id_level = 2

        # kategorie určená mytologickým postavám a bohům
        elif re.search(r"\[\[\s*Kategorie:\s*Hrdinové\s+a\s+postavy\s+řecké\s+mytologie(?:\|[^]]*)?\]\]", content, re.I) or re.search(r"\[\[\s*Kategorie:[\w\s]+bohové(?:\|[^]]*)?\]\]", content, re.I):
            id_level = 2

        # kategorie určená fiktivním postavám
        elif re.search(r"\[\[\s*Kategorie:\s*Postavy[^]]*\]\]", content, re.I):
            id_level = 2

        # vrací pravděpodobnost, že je stránka na základě kategorií o osobě
        return id_level

    def get_data(self, content):
        """
        Extrahuje data o osobě z obsahu stránky.

        Parametry:
        content - obsah stránky (str)
        """
        # prefix - fiktivní osoby
        if self.prefix != "person:fictional":
            if re.search(r"\[\[\s*Kategorie:\s*Hrdinové\s+a\s+postavy\s+řecké\s+mytologie(?:\|[^]]*)?\]\]", content, re.I) or \
               re.search(r"\[\[\s*Kategorie:[\w\s]+bohové(?:\|[^]]*)?\]\]", content, re.I) or \
               re.search(r"\[\[\s*Kategorie:\s*Postavy[^]]*\]\]", content, re.I):
                self.prefix = "person:fictional"

        if self.prefix != "person:group":
            natToKB = NatToKB()
            nationalities = natToKB.get_nationalities()

            name_without_location = re.sub(r"\s+(?:ze?|of|von)\s+.*", "", self.title, flags=re.I)
            a_and_neighbours = re.search(r"((?:[^ ])+)\s+a(?:nd)?\s+((?:[^ ])+)", name_without_location)
            if a_and_neighbours:
                if a_and_neighbours.group(1) not in nationalities or a_and_neighbours.group(2) not in nationalities:
                    self.prefix = "person:group"
                # else Kateřina Řecká a Dánská" is regular person


        # pohlaví
        if not self.gender:
            if re.search(r"\[\[\s*Kategorie:\s*Muži(?:\|[^]]*)?\]\]", content, re.I):
                self.gender = "M"
            elif re.search(r"\[\[\s*Kategorie:\s*Ženy(?:\|[^]]*)?\]\]", content, re.I):
                self.gender = "F"
            else:
                infobox_gender = re.search(r"\|\s*pohlaví\s*=\s*([^\s]+)", content, re.I)
                if infobox_gender and infobox_gender.group(1):
                    infobox_gender = infobox_gender.group(1).lower()
                    if infobox_gender == "muž":
                        self.gender = "M"
                    elif infobox_gender == "žena":
                        self.gender = "F"

        try:
            data = content.splitlines()
        except AttributeError:
            pass
        else:
            for ln in data:
                # aliasy
                rexp_format = r"(jiná[\s_]+jména|(?:rodné|celé|úplné|posmrtné|chrámové|trůnní)[\s_]+jméno|pseudonym|přezdívka)\s*=(?!=)\s+(?!nezveřejněn[aáéoý]?|neznám[aáéoý]?)(.*)"
                rexp = re.search(rexp_format, ln, re.I)
                if rexp and rexp.group(2):
                    nametype = None
                    tmp_alias = rexp.group(2)

                    if rexp.group(1):
                        tmp_name_type = rexp.group(1).lower()
                        if tmp_name_type == "pseudonym":
                            nametype = self.NT_PSEUDO
                        elif tmp_name_type == "přezdívka":
                            nametype = self.NT_NICK
                        elif tmp_name_type == "rodné jméno":
                            alias_spaces = len(re.findall(r"[^\s]+\s+[^\s]+", tmp_alias))
                            if not alias_spaces:
                                tmp_alias_new, was_replaced = re.subn(r"(?<=\s)(?:ze?|of|von)\s+.*", tmp_alias, self.title, flags=re.I)
                                if was_replaced:
                                    tmp_alias = tmp_alias_new
                                else:
                                    tmp_alias = re.sub(r"[^\s]+$", tmp_alias, self.title)

                    tmp_alias = re.sub(r"^\s*německyː\s*", "", tmp_alias, flags = re.I) # https://cs.wikipedia.org/wiki/Marie_Gabriela_Bavorská =>   | celé jméno = německyː ''Marie Gabrielle Mathilde Isabelle Therese Antoinette Sabine Herzogin in Bayern''
                    tmp_alias = re.sub(r"^\s*(?:viz\s+)?\[\[[^\]]+\]\]", "", tmp_alias, flags = re.I) # https://cs.wikipedia.org/wiki/T%C3%BArin =>   | přezdívka = viz [[Túrin#Jména, přezdívky a tituly|Jména, přezdívky a tituly]]
                    self.get_aliases(self.del_redundant_text(tmp_alias), nametype = nametype)
                    continue

                if (self.gender == "F"):
                    female_variant = self.title[:-3] if self.title[-3:] == "ová" else self.title + "ová"
                    if self.title in self.redirects and female_variant in self.redirects[self.title]:
                        self.aliases[female_variant] = self.LANG_CZECH if self.title[-3:] == "ová" else None

                # obrázek - infobox
                rexp = re.search(r"obrázek\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázky - ostatní
                rexp = re.search(r"\[\[(?:Soubor|File):([^|]+?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg))(?:\|.*?)?\]\]", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(rexp.group(1))
                    continue

                # datum narození
                rexp = re.search(r"datum[\s_]narození\s+=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_birth_date(self.del_redundant_text(rexp.group(1)))
                    continue

                # datum úmrtí
                rexp = re.search(r"datum[\s_]úmrtí\s+=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_death_date(self.del_redundant_text(rexp.group(1)))
                    continue

                # místo narození
                rexp = re.search(r"místo[\s_]narození\s+=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_place(self.del_redundant_text(rexp.group(1)), True)
                    continue

                # místo úmrtí
                rexp = re.search(r"místo[\s_]úmrtí\s+=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_place(self.del_redundant_text(rexp.group(1)), False)
                    continue

                # zaměstnání/profese
                rexp = re.search(r"(?:profese|zaměstnání|povolání)\s*=(?!=)\s*(.*)", ln, flags=re.I)
                if rexp and rexp.group(1):
                    self.get_jobs(self.del_redundant_text(rexp.group(1)))
                    continue

                # národnost
                rexp = re.search(r"národnost\s*=(?!=)\s*(.*)", ln, flags=re.I)
                if rexp and rexp.group(1):
                    if not self.nationality:
                        self.get_nationality(self.del_redundant_text(rexp.group(1)))
                    continue

                # první věta
                if not self.description and not re.search(r"^\s*({{Infobox|\|)", ln, flags=re.I):
                    abbrs = "".join((r"(?<!\s(?:tzv|at[pd]|roz))", r"(?<!\s(?:apod|(?:ku|na|po)př|příp))", r"(?<!\s[amt]j)", r"(?<!\d)"))
                    rexp = re.search(r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|patř(?:í|il)|stal).*?" + abbrs + "\.(?![^[]*?\]\])", ln)
                    if rexp:
                        self.get_first_sentence(self.del_redundant_text(rexp.group(0), ", "))

                        tmp_first_sentence = rexp.group(0)
                        fs_first_aliases = []
                        # extrakce alternativních pojmenování z první věty
                        #  '''Jiří''' (též '''Jura''') '''Mandel''' -> vygenerovat "Jiří Mandel" a "Jura Mandel" (negenerovat "Jiří", "Jura", "Mandel")
                        tmp_fs_first_aliases = regex.search(r"^((?:'{3}(?:[\"\p{L} ]|'(?!''))+'{3}\s+)+)\((?:(?:někdy|nebo)?\s*(?:také|též|rozená))?\s*(?:('{3}[^\)]+'{3}))?(?:'(?!'')|[^\)])*\)\s*((?:'{3}\p{L}+'{3}\s+)*)(.*)", tmp_first_sentence, flags = re.I)
                        if tmp_fs_first_aliases:
                            fs_fa_before_bracket = tmp_fs_first_aliases.group(1).strip()
                            fs_fa_after_bracket = tmp_fs_first_aliases.group(3).strip()
                            fs_first_aliases.append(fs_fa_before_bracket + " " + fs_fa_after_bracket)
                            if tmp_fs_first_aliases.group(2):
                                name_variants = re.findall(r"'{3}(.+?)'{3}", tmp_fs_first_aliases.group(2).strip())
                                if name_variants:
                                    for name_variant in name_variants:
                                        fs_first_aliases.append(re.sub("[^ ]+$", name_variant, fs_fa_before_bracket) + " " + fs_fa_after_bracket)
                            tmp_first_sentence = tmp_fs_first_aliases.group(4)
                        else:
                            #  '''Jiří''' '''Jindra''' -> vygenerovat "Jiří Jindra" (negenerovat "Jiří" a "Jindra")
                            tmp_fs_first_aliases = regex.search(r"^((?:'{3}\p{L}+'{3}\s+)+)(.*)", tmp_first_sentence)
                            if tmp_fs_first_aliases:
                                fs_first_aliases.append(tmp_fs_first_aliases.group(1).strip())
                                tmp_first_sentence = tmp_fs_first_aliases.group(2).strip()

                        fs_aliases = re.findall(r"'{3}(.+?)'{3}", tmp_first_sentence)
                        if not fs_aliases:
                            fs_aliases = []
                        fs_aliases += fs_first_aliases

                        for fs_alias in fs_aliases:
                            self.get_aliases(self.del_redundant_text(fs_alias).strip("'"))
                        continue


    def get_birth_date(self, date):
        """
        Převádí datum narození osoby do jednotného formátu.

        Parametry:
        date - datum narození osoby (str)
        """
        if self.birth_date:
            return

        modif_date = self._convert_date(date, True)

        self.birth_date = modif_date


    def custom_transform_alias(self, alias):
        """
        Umožňuje provádět vlastní transformace aliasů entity do jednotného formátu.

        Parametry:
        alias - alternativní pojmenování entity (str)
        """

        # u titulů bez teček je třeba kontrolova mezeru, čárku nebo konec (například MA jinak vezme následující příjmení začínající "Ma..." a bude toto jméno považovat za součást předchozího)
        alias = re.sub(r", (?!(J[rn]\.?|Sr\.?|ml(?:\.|adší)?|[PT]h\.?D\.?|MBA|M\.?A\.?|M\.?S\.?|M\.?Sc\.?|CSc\.|D(?:\.|r\.?)Sc\.|DiS\.|CC)(\.|,| |$))", "|", alias, flags=re.I)
#        alias = re.sub(r"^(?:prof|doc)\.)?\s*((BcA?\.|Ing\.(\s*arch\.)?|M[SDUV]Dr\.|Mg[Ar]\.|(?:JU|Ph|RN|Pharm|Th|Paed)Dr\.|PhMr\.|ThMgr\.|R[CST]Dr\.|Dr.)(\s+et)?\s*)*", "", alias, flags=re.I) # pro zničení titulů před jménem
        return alias


    def get_death_date(self, date):
        """
        Převádí datum úmrtí osoby do jednotného formátu.

        Parametry:
        date - datum úmrtí osoby (str)
        """
        if self.death_date:
            return

        modif_date = self._convert_date(date, False)

        self.death_date = modif_date

    def get_first_sentence(self, fs):
        """
        Převádí první větu stránky do jednotného formátu a získává z ní popis a datum a místo narození/úmrtí.

        Parametry:
        fs - první věta stránky (str)
        """
        #TODO: refactorize
        fs = re.sub(r"{{(?:vjazyce2|cizojazyčně|audio|cj)\|.*?\|(.+?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{IPA\d?\|(.+?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{výslovnost\|(.+?)\|.*?}}", r"\1", fs, flags=re.I)
        fs = self._subx(r".*?{{\s*datum[\s_]+(?:narození|úmrtí)\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*", lambda x: self._regex_date(x, 3), fs, flags=re.I)
        fs = self._subx(r".*?{{\s*JULGREGDATUM\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)[^}]*}}.*", lambda x: self._regex_date(x, 4), fs, flags=re.I)
        fs = re.sub(r"{{čínsky(.+?)}}", lambda x: re.sub("(?:znaky|pchin-jin|tradiční|zjednodušené|pinyin)\s*=\s*(.*?)(?:\||}})", r"\1 ", x.group(1), flags=re.I), fs, flags=re.I)
        fs = re.sub(r"{{malé\|(.*?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"^\s*}}", "", fs) # Eliminate the end of a template

        self.description = fs

        # získání data/místa narození/úmrtí z první věty - začátek
        # (* 2000)
        if not self.birth_date:
            rexp = re.search(r"\(\s*\*\s*(\d+)\s*\)", fs)
            if rexp and rexp.group(1):
                self.get_birth_date(rexp.group(1))

        # (* 1. ledna 2000)
        if not self.birth_date:
            rexp = re.search(r"\(\s*\*\s*(\d+\.\s*\w+\.?\s+\d{1,4})\s*\)", fs)
            if rexp and rexp.group(1):
                self.get_birth_date(rexp.group(1))

        # (* 1. ledna 2000, Brno), (* 1. ledna 200 Brno, Česká republika)
        if not self.birth_date or not self.birth_place:
            rexp = re.search(r"\(\s*\*\s*(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])\s*(?![\-–—−])\)", fs)
            if rexp:
                if rexp.group(1) and not self.birth_date:
                    self.get_birth_date(rexp.group(1))
                if rexp.group(2) and not self.birth_place:
                    self.get_place(rexp.group(2), True)

        # (* 2000 – † 2018), (* 2000, Brno - † 2018 Brno, Česká republika)
        if not self.birth_date or not self.death_date or not self.birth_place or not self.death_place:
            rexp = re.search(r"\(\s*(?:\*\s*)?(\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*[\-–—−]\s*(?:†\s*)?(\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*\)", fs)
            if rexp:
                if rexp.group(1) and not self.birth_date:
                    self.get_birth_date(rexp.group(1))
                if rexp.group(2) and not self.birth_place:
                    self.get_place(rexp.group(2), True)
                if rexp.group(3) and not self.death_date:
                    self.get_death_date(rexp.group(3))
                if rexp.group(4) and not self.death_place:
                    self.get_place(rexp.group(4), False)

        # (* 1. ledna 2000 – † 1. ledna 2018), (* 1. ledna 2000, Brno - † 1. ledna 2018 Brno, Česká republika)
        if not self.birth_date or not self.death_date or not self.birth_place or not self.death_place:
            rexp = re.search(r"\(\s*(?:\*\s*)?(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*[\-–—−]\s*(?:†\s*)?(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*\)", fs)
            if rexp:
                if rexp.group(1) and not self.birth_date:
                    self.get_birth_date(rexp.group(1))
                if rexp.group(2) and not self.birth_place:
                    self.get_place(rexp.group(2), True)
                if rexp.group(3) and not self.death_date:
                    self.get_death_date(rexp.group(3))
                if rexp.group(4) and not self.death_place:
                    self.get_place(rexp.group(4), False)
        # získání data/místa narození/úmrtí z první věty - konec

    def get_jobs(self, job):
        """
        Převádí zaměstnání osoby do jednotného formátu.

        Parametry:
        job - zaměstnání osoby (str)
        """
        job = re.sub(r"(?:Soubor|File):.*?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)(?:\|[\w\s]+)?\|[\w\s]+\|[\w\s]+(?:,\s*)?", "", job, flags=re.I)
        job = re.sub(r"\d+\s*px", "", job, flags=re.I)
        job = re.sub(r"^[\s,]+", "", job)
        job = re.sub(r"\[.*?\]", "", job)
        job = re.sub(r"\s*/\s*", ", ", job)
        job = re.sub(r"\s+", " ", job).strip().strip(".,;")

        if ";" in job:
            job = re.sub(r"\s*;\s*", "|", job)
        else:
            job = re.sub(r"\s*,\s*", "|", job)

        self.jobs = job if not self.jobs else "|" + job

    def get_nationality(self, nationality):
        """
        Převádí národnost osoby do jednotného formátu

        Parametry:
        nationality - národnost osoby (str)
        """
        nationality = re.sub(r"{{Vlajka a název\|(.*?)(?:\|.*?)?}}", r"\1", nationality, flags=re.I)
        nationality = re.sub(r"{{malé\|(.*?)}}", r"\1", nationality, flags=re.I)
        nationality = re.sub(r"{{.*?}}", "", nationality)
        nationality = re.sub(r"<.*?>", "", nationality)
        nationality = re.sub(r"(.*?)\|.*$", r"\1", nationality)
        nationality = re.sub(r"\d+\s*px", "", nationality, flags=re.I)
        nationality = re.sub(r"\(.*?\)", "", nationality)
        nationality = re.sub(r"\s+", " ", nationality).strip().strip(".,;")
        nationality = re.sub(r"\s*[,;/]\s*|\s+(?:či|[\-–—−]|a|nebo)\s+", "|", nationality)

        self.nationality = nationality

    def get_place(self, place, is_birth):
        """
        Převádí místo narození/úmrtí osoby do jednotného formátu.

        Parametry:
        place - místo narození/úmrtí osoby (str)
        is_birth - určuje, zda se jedná o místo narození, či úmrtí (bool)
        """
        place = re.sub(r"{{Vlajka a název\|(.*?)(?:\|.*?)?}}", r"\1", place, flags=re.I)
        place = re.sub(r"{{(?:vjazyce2|cizojazyčně|audio|cj)\|.*?\|(.+?)}}", r"\1", place, flags=re.I)
        place = re.sub(r"{{malé\|(.*?)}}", r"\1", place, flags=re.I)
        place = re.sub(r"{{.*?}}", "", place)
        place = re.sub(r"<.*?>", "", place)
        place = re.sub(r"(?:Soubor|File):.*?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)(?:\|[\w\s]+)?\|[\w\s]+\|[\w\s]+(?:,\s*)?", "", place, flags=re.I)
        place = re.sub(r"\d+\s*px", "", place, flags=re.I)
        place = re.sub(r"(?:(?:,\s*)?\(.*?věk.*?\)$|\(.*?věk.*?\)(?:,\s*)?)", "", place, flags=re.I)
        place = re.sub(r"\(.*?let.*?\)", "", place, flags=re.I)
        place = re.sub(r",{2,}", ",", place)
        place = re.sub(r"[{}<>\[\]]", "", place)
        place = re.sub(r"\s+", " ", place).strip().strip(",")

        if is_birth:
            self.birth_place = place
        else:
            self.death_place = place

    def write_to_file(self):
        """
        Zapisuje údaje o osobě do znalostní báze.
        """
        with open("kb_cs", "a", encoding="utf-8") as fl:
            fl.write(self.eid + "\t")
            fl.write(self.prefix + "\t")
            fl.write(self.title + "\t")
            fl.write((self.serialize_aliases() if self.prefix != "person:group" else "") + "\t")
            fl.write(self.description + "\t")
            fl.write(self.original_title + "\t")
            fl.write(self.images + "\t")
            fl.write(self.link + "\t")
            fl.write(self.gender + "\t")
            fl.write(self.birth_date + "\t")
            fl.write(self.birth_place + "\t")
            fl.write(self.death_date + "\t")
            fl.write(self.death_place + "\t")
            fl.write(self.jobs + "\t")
            fl.write(self.nationality + "\n")

    def _convert_date(self, date, is_birth):
        """
        Zpracuje a konvertuje datum narození/úmrtí osoby do jednotného formátu.

        Parametry:
        date - datum narození/úmrtí osoby (str)
        is_birth - určuje, zda se jedná o datum narození, či úmrtí (bool)

        Návratové hodnoty:
        Datum narození/úmrtí osoby v jednotném formátu. (str)
        """

        # detekce př. n. l.
        date_bc = True if re.search(r"př\.?\s*n\.?\s*l\.?", date, re.I) else False

        # datum před úpravou
        orig_date = date[:]

        # odstranění přebytečného textu
        date = date.replace("?", "").replace("~", "")
        date = re.sub(r"{{(?!\s*datum|\s*julgreg)[^}]+}}", "", date, flags=re.I)
        date = re.sub(r"př\.\s*n\.\s*l\.", "", date, flags=re.I)

        # staletí - začátek
        date = self._subx(r".*?(\d+\.?|prvn.|druh.)\s*(?:pol(?:\.|ovin.))\s*(\d+)\.?\s*(?:st(?:\.?|ol\.?|oletí)).*",
                    lambda x: self._regex_date(x, 0), date, flags=re.I)

        date = self._subx(r".*?(\d+)\.?\s*(?:až?|[\-–—−/])\s*(\d+)\.?\s*(?:st\.?|stol\.?|století).*",
                    lambda x: self._regex_date(x, 1), date, flags=re.I)

        date = self._subx(r".*?(\d+)\.?\s*(?:st\.?|stol\.?|století).*",
                    lambda x: self._regex_date(x, 2), date, flags=re.I)
        # staletí - konec

        # data z šablon - začátek
        if is_birth:
            date = self._subx(r".*?{{\s*datum[\s_]+narození\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*",
                        lambda x: self._regex_date(x, 3), date, flags=re.I)
        else:
            date = self._subx(r".*?{{\s*datum[\s_]+úmrtí\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*",
                        lambda x: self._regex_date(x, 3), date, flags=re.I)
        date = self._subx(r".*?{{\s*JULGREGDATUM\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)[^}]*}}.*",
                    lambda x: self._regex_date(x, 4), date, flags=re.I)
        # data z šablon - konec

        # data napsaná natvrdo - začátek
        date = self._subx(r".*?(\d+)\.\s*((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+)(?:\s*,)?\s+(\d+).*",
                    lambda x: self._regex_date(x, 8), date, flags=re.I)
        date = self._subx(r".*?(\d+)\s*(?:či|až?|nebo|[\-–—−/])\s*(\d+).*",
                    lambda x: self._regex_date(x, 5), date, flags=re.I)
        date = self._subx(r".*?(\d+)\s*\.\s*(\d+)\s*\.\s*(\d+).*", lambda x: self._regex_date(x, 4), date)
        date = self._subx(r".*?((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+)(?:\s*,)?\s+(\d+).*",
                    lambda x: self._regex_date(x, 9), date, flags=re.I)
        date = self._subx(r".*?(\d+)\.\s*((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+).*",
                    lambda x: self._regex_date(x, 7), date, flags=re.I)
        date = self._subx(r".*?(\d{1,4}).*", lambda x: self._regex_date(x, 6), date)
        # data napsaná natvrdo - konec

        # odstranění zdvojených bílých znaků a jejich převod na mezery
        date = self._subx(r"\s+", " ", date).strip()

        # odstranění nezkonvertovatelných dat
        date = "" if orig_date == date else date

        # převod na formát data před naším letopočtem - začátek
        if date and date_bc:
            rexp = re.search(r"^([\d?]{4})-([\d?]{2})-([\d?]{2})$", date)
            if rexp and rexp.group(1):
                if rexp.group(1) != "????":
                    bc_year = "-" + str(int(rexp.group(1)) - 1).zfill(4) if rexp.group(1) != "0001" else "0000"
                    date = "{}-{}-{}".format(bc_year, rexp.group(2), rexp.group(3))
            else:
                rexp = re.search(r"^([\d?]{4})-([\d?]{2})-([\d?]{2})/([\d?]{4})-([\d?]{2})-([\d?]{2})$", date)
                if rexp and rexp.group(1) and rexp.group(4):
                    if rexp.group(1) != "????" and rexp.group(4) != "????":
                        yr1, yr2 = int(rexp.group(1)), int(rexp.group(4))
                        if yr1 < yr2:  # prohození hodnot, pokud je první rok menší než druhý
                            yr1, yr2 = yr2, yr1
                        bc_year1 = "-" + str(yr1 - 1).zfill(4) if yr1 != 1 else "0000"
                        bc_year2 = "-" + str(yr2 - 1).zfill(4) if yr2 != 1 else "0000"
                        date = "{}-{}-{}/{}-{}-{}".format(bc_year1, rexp.group(2), rexp.group(3), bc_year2,
                                                          rexp.group(6), rexp.group(6))
        # převod na formát data před naším letopočtem - konec

        return date

    @staticmethod
    def _get_cal_month(month):
        """
        Převádí název kalendářního měsíce na číselný tvar.

        Parametry:
        month - název měsíce (str)

        Návratové hodnoty:
        Číslo kalendářního měsíce na 2 pozicích, jinak ??. (str)
        """

        cal_months_part = ["led", "únor", "břez", "dub", "květ", "červ", "červen", "srp", "září", "říj", "listopad",
                           "prosin"]

        for idx, mon in enumerate(cal_months_part, 1):
            if mon in month.lower():
                if idx == 6 and "c" in month:  # v případě špatné identifikace června a července v některých pádech
                    return "07"
                return str(idx).zfill(2)

        return "??"

    def _regex_date(self, match_obj, match_type):
        """
        Převádí předaný match object na jednotný formát data dle standardu ISO 8601.

        Parametry:
        match_obj  - match object (MatchObject)
        match_type - určuje, jaký typ formátu se má aplikovat (int)

        Návratová hodnota:
        Jednotný formát data. (str)
        """
        if match_type == 0:
            f = "{:04d}-??-??/{:04d}-??-??"
            if re.search(r"1\.?|prvn.", match_obj.group(1), re.I):
                f = f.format((int(match_obj.group(2)) - 1) * 100 + 1, int(match_obj.group(2)) * 100 - 50)
            else:
                f = f.format((int(match_obj.group(2)) - 1) * 100 + 51, int(match_obj.group(2)) * 100)
            return f

        if match_type == 1:
            f = "{:04d}-??-??/{:04d}-??-??"
            return f.format((int(match_obj.group(1)) - 1) * 100 + 1, int(match_obj.group(2)) * 100)

        if match_type == 2:
            f = "{:04d}-??-??/{:04d}-??-??"
            return f.format((int(match_obj.group(1)) - 1) * 100 + 1, int(match_obj.group(1)) * 100)

        if match_type == 3:
            f = "{}-{}-{}"
            year = "????" if not match_obj.group(1) else match_obj.group(1).zfill(4)
            month = "??" if not match_obj.group(2) else match_obj.group(2).zfill(2)
            day = "??" if not match_obj.group(3) else match_obj.group(3).zfill(2)
            return f.format(year, month, day)

        if match_type == 4:
            f = "{}-{}-{}"
            return f.format(match_obj.group(3).zfill(4), match_obj.group(2).zfill(2), match_obj.group(1).zfill(2))

        if match_type == 5:
            return "{}-??-??/{}-??-??".format(match_obj.group(1).zfill(4), match_obj.group(2).zfill(4))

        if match_type == 6:
            return "{}-??-??".format(match_obj.group(1).zfill(4))

        if match_type == 7:
            f = "????-{}-{}"
            return f.format(self._get_cal_month(match_obj.group(2)), match_obj.group(1).zfill(2))

        if match_type == 8:
            f = "{}-{}-{}"
            return f.format(match_obj.group(3).zfill(4), self._get_cal_month(match_obj.group(2)),
                            match_obj.group(1).zfill(2))

        if match_type == 9:
            f = "{}-{}-??"
            return f.format(match_obj.group(2).zfill(4), self._get_cal_month(match_obj.group(1)))

    @staticmethod
    def _subx(pattern, repl, string, count=0, flags=0):
        """
        Vykonává totožný úkon jako funkce sub z modulu re, ale jen v případě, že nenarazí na datum ve standardizovaném formátu.

        Parametry:
        pattern - vzor (str)
        repl - náhrada (str)
        string - řetězec, na kterém má být úkon proveden (str)
        count - počet výskytů, na kterých má být úkon proveden (int)
        flags - speciální značky, které ovlivňují chování funkce (int)
        """
        if re.match(r"[\d?]+-[\d?]+-[\d?]+", string):
            return string
        return re.sub(pattern, repl, string, count, flags)
