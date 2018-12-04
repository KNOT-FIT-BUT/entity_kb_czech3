#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje třídu 'EntSettlement', která uchovává údaje o sídlech.

Poznámky:
Infobox - sídlo
Infobox - sídlo světa
Infobox - česká obec
Infobox - statutární město
Infobox anglické město
"""

import re
from ent_core import EntCore


class EntSettlement(EntCore):
    """
    Třída určená pro sídla.

    Instanční atributy:
    title - název sídla (str)
    prefix - prefix entity (str)
    eid - ID entity (str)
    link - odkaz na Wikipedii (str)
    aliases - alternativní pojmenování sídla (str)
    description - stručný popis sídla (str)
    images - absolutní cesty k obrázkům Wikimedia Commons (str)

    area - rozloha sídla v kilometrech čtverečních (str)
    country - stát, ke kterému sídlo patří (str)
    population - počet obyvatel sídla (str)
    """

    def __init__(self, title, prefix, link, redirects):
        """
        Inicializuje třídu 'EntSettlement'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntSettlement, self).__init__(title, prefix, link, redirects)

        self.area = ""
        self.country = ""
        self.population = ""

    @classmethod
    def is_settlement(cls, title, content):
        """
        Na základě názvu a obsahu stránky určuje, zda stránka pojednává o sídlu, či nikoliv.

        Parametry:
        title - název stránky (str)
        content - obsah stránky (str)

        Návratové hodnoty:
        Dvojice hodnot (level, type); level určuje, zda stránka pojednává o sídlu, type určuje způsob, kterým byla stránka identifikována. (Tuple[int, str])
        """
        id_level = 0
        id_type = ""

        # kontrola šablon
        id_level, id_type = cls._contains_settlement_infoboxes(content, id_level, id_type)

        # kontrola kategorií
        id_level, id_type = cls._contains_settlement_categories(title, content, id_level, id_type)

        return id_level, id_type

    @staticmethod
    def _contains_settlement_infoboxes(content, id_level, id_type):
        """
        Kontroluje, zda obsah stránky obsahuje některý z infoboxů, které identifikují stránky o sídlech.

        Parametry:
        content - obsah stránky (str)
        id_level - nerovná-li se nule, kontrola se již neprovádí (int)
        id_type - způsob identifikace sídla (str)

        Návratová hodnota:
        Dvojice hodnot (level, type); level určuje, zda stránka pojednává o sídlu, type určuje způsob, kterým byla stránka identifikována. (Tuple[int, str])
        """
        # není-li id_level roven nule, kontrola se již neprovádí
        if id_level:
            return id_level, id_type

        # kontrola probíhá dál
        ib_prefix = r"{{\s*Infobox\s+"

        if re.search(ib_prefix + r"-\s+sídlo", content, re.I):
            return 1, "Sídlo (světa)"
        if re.search(ib_prefix + r"-\s+česká\s+obec", content, re.I):
            return 1, "Česká obec"
        if re.search(ib_prefix + r"katastrální\s+území\s+Prahy", content, re.I):
            return 1, "Česká obec"
        if re.search(ib_prefix + r"-\s+statutární\s+město", content, re.I):
            return 1, "Statutární město"
        if re.search(ib_prefix + r"anglické\s+město", content, re.I):
            return 1, "Anglické město"
        return 0, ""

    @staticmethod
    def _contains_settlement_categories(title, content, id_level, id_type):
        """
        Kontroluje, zda obsah stránky obsahuje některou z kategorií, které identifikují stránky o sídlech.

        Parametry:
        title - název stránky (str)
        content - obsah stránky (str)
        id_level - nerovná-li se nule, kontrola se již neprovádí (int)
        id_type - způsob identifikace sídla (str)

        Návratová hodnota:
        Pravděpodobnost, že je stránka o sídlu. (int)
        """
        # není-li id_level roven nule, kontrola se již neprovádí
        if id_level:
            return id_level, id_type

        # kontrola probíhá dál
        id_level, id_type = 0, ""
        content = content.replace("[ ", "[").replace(" ]", "]")

        if re.search(r"\[\[Kategorie:Města\s+(?:na|ve?)\s+.+?\]\]", content, re.I):
            id_level, id_type = 2, "Kategorie Města..."
        elif re.search(r"\[\[Kategorie:Obce\s+(?:na|ve?)\s+.+?\]\]", content, re.I):
            id_level, id_type = 2, "Kategorie Obce..."

        if any(x in title.lower() for x in ("obec", "obc", "měst", "metro", "sídel", "sídl", "komun", "muze", "místo", "vesnic")):
            id_level, id_type = 0, ""

        return id_level, id_type

    def get_data(self, content):
        """
        Extrahuje data o sídlu z obsahu stránky.

        Parametry:
        content - obsah stránky (str)
        """
        content = content.replace("&nbsp;", " ")
        content = re.sub(r"m\sn\.\s*", "metrů nad ", content)

        try:
            data = content.splitlines()
        except AttributeError:
            pass
        else:
            for ln in data:
                # aliasy
                rexp_format = r"\|\s*jméno\s*=(?!=)\s*(.*)"
                rexp = re.search(rexp_format, ln, re.I)
                if rexp and rexp.group(1):
                    self.get_aliases(self.del_redundant_text(rexp.group(1)), True)
                    continue

                rexp_format = r"(?:název|(?:originální[\s_]+)?jméno)\s*=(?!=)\s*(.*)"
                rexp = re.search(rexp_format, ln, re.I)
                if rexp and rexp.group(1):
                    self.get_aliases(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázek - infobox
                rexp = re.search(r"(?:obrázek|vlajka|znak|logo)\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázky - ostatní
                rexp = re.search(r"\[\[(?:Soubor|File):([^|]+?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg))(?:\|.*?)?\]\]",
                                 ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(rexp.group(1))
                    continue

                # země
                if not self.country and re.search(r"{{\s*Infobox\s+-\s+(?:česká\s+obec|statutární\s+město)", ln, re.I):
                    self.country = "Česká republika"
                    continue

                if not self.country and re.search(r"{{\s*Infobox\s+anglické\s+město", ln, re.I):
                    self.country = "Spojené království"
                    continue

                if not self.country:
                    rexp = re.search(r"(?:země|stát)\s*=(?!=)\s*(.*)", ln, re.I)
                    if rexp and rexp.group(1):
                        self.get_country(self.del_redundant_text(rexp.group(1)))
                        continue

                # počet obyvatel
                rexp = re.search(r"po[cč]et[\s_]obyvatel\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_population(self.del_redundant_text(rexp.group(1)))
                    continue

                # rozloha
                rexp = re.search(r"(?:rozloha|výměra)\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_area(self.del_redundant_text(rexp.group(1)))
                    continue

                # první věta
                abbrs = "".join((r"(?<!\s(?:tzv|at[pd]))", r"(?<!\s(?:apod|(?:ku|na|po)př|příp))", r"(?<!\s(?:[amt]j|fr))", r"(?<!\d)", r"(?<!nad m)"))
                rexp = re.search(r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|nacház(?:í|ejí)|patř(?:í|il)|stal|rozprostír|lež(?:í|el)).*?" + abbrs + "\.(?![^[]*?\]\])", ln)
                if rexp:
                    if not self.description:
                        self.get_first_sentence(self.del_redundant_text(rexp.group(0), ", "))

                        # extrakce alternativních pojmenování z první věty
                        fs_aliases = re.findall(r"'{3}(.+?)'{3}", rexp.group(0))
                        if fs_aliases:
                            for fs_alias in fs_aliases:
                                self.get_aliases(self.del_redundant_text(fs_alias).strip("'"))
                    continue


    def custom_transform_alias(self, alias):
        """
        Vlastní transformace aliasu.

        Parametry:
        alias - alternativní pojmenování entity (str)
        """

        return self.transform_geo_alias(alias)


    def get_area(self, area):
        """
        Převádí rozlohu sídla do jednotného formátu.

        Parametry:
        area - rozloha/výměra sídla (str)
        """
        area = re.sub(r"\(.*?\)", "", area)
        area = re.sub(r"\[.*?\]", "", area)
        area = re.sub(r"<.*?>", "", area)
        area = re.sub(r"{{.*?}}", "", area).replace("{", "").replace("}", "")
        area = re.sub(r"(?<=\d)\s(?=\d)", "", area).strip()
        area = re.sub(r"(?<=\d)\.(?=\d)", ",", area)
        area = re.sub(r"^\D*(?=\d)", "", area)
        area = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", area)
        area = "" if not re.search(r"\d", area) else area

        self.area = area

    def get_country(self, country):
        """
        Převádí stát, ke kterému sídlo patří, do jednotného formátu.

        Parametry:
        country - země, ke které sídlo patří (str)
        """
        country = re.sub(r"{{vlajka\s+a\s+název\|(.*?)}}", r"\1", country, flags=re.I)
        country = re.sub(r"{{.*?}}", "", country)
        country = "Česká republika" if re.search(r"Čechy|Morava|Slezsko", country, re.I) else country
        country = re.sub(r",?\s*\(.*?\)", "", country)
        country = re.sub(r"\s+", " ", country).strip().replace("'", "")

        self.country = country

    def get_first_sentence(self, fs):
        """
        Převádí první větu stránky do jednotného formátu a získává z ní popis.

        Parametry:
        fs - první věta stránky (str)
        """
        #TODO: refactorize
        fs = re.sub(r"\(.*?\)", "", fs)
        fs = re.sub(r"\[.*?\]", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(r"{{(?:cj|cizojazyčně|vjazyce\d?)\|\w+\|(.*?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
        fs = re.sub(r"/.*?/", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"}}", "", fs) # Eliminate the end of a template
        fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",")

        self.description = fs

    def get_population(self, population):
        """
        Převádí počet obyvatel sídla do jednotného formátu.

        Parametry:
        population - počet obyvatel sídla (str)
        """
        coef = 1000000 if re.search(r"mil\.|mili[oó]n", population, re.I) else 1000 if re.search(r"tis\.|tis[ií]c", population, re.I) else 0

        population = re.sub(r"\(.*?\)", "", population)
        population = re.sub(r"\[.*?\]", "", population)
        population = re.sub(r"<.*?>", "", population)
        population = re.sub(r"{{.*?}}", "", population).replace("{", "").replace("}", "")
        population = re.sub(r"(?<=\d)[,.\s](?=\d)", "", population).strip()
        population = re.sub(r"^\D*(?=\d)", "", population)
        population = re.sub(r"^(\d+)\D.*$", r"\1", population)
        population = "" if not re.search(r"\d", population) else population

        if coef and population:
            population = str(int(population) * coef)

        self.population = population

    def write_to_file(self):
        """
        Zapisuje údaje o sídlu do znalostní báze.
        """
        with open("kb_cs", "a", encoding="utf-8") as fl:
            fl.write(self.eid + "\t")
            fl.write(self.prefix + "\t")
            fl.write(self.title + "\t")
            fl.write(self.serialize_aliases() + "\t")
            fl.write(self.description + "\t")
            fl.write(self.original_title + "\t")
            fl.write(self.images + "\t")
            fl.write(self.link + "\t")
            fl.write(self.country + "\t")
            fl.write(self.area + "\t")
            fl.write(self.population + "\n")
