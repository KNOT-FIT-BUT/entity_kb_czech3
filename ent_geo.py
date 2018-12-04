#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje třídu 'EntGeo', která uchovává údaje o geografických entitách.
"""

import re
from ent_core import EntCore


class EntGeo(EntCore):
    """
    Třída určená pro geografické entity.

    Instanční atributy:
    title - název geografické entity (str)
    prefix - prefix entity (str)
    eid - ID entity (str)
    link - odkaz na Wikipedii (str)
    aliases - alternativní pojmenování geografické entity (str)
    description - stručný popis geografické entity (str)
    images - absolutní cesty k obrázkům Wikimedia Commons (str)

    area - rozloha geografické entity v kilometrech čtverečních (str)
    continent - světadíl, na kterém geografická entita leží (str)
    latitude - zeměpisná šířka geografické entity (str)
    longitude - zeměpisná délka geografické entity (str)
    population - počet obyvatel, jenž žije na území geografické entity (str)
    total_height - celková výška vodopádu (str)

    subtype - podtyp geografické entity (str)
    """

    def __init__(self, title, prefix, link, redirects):
        """
        Inicializuje třídu 'EntGeo'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntGeo, self).__init__(title, prefix, link, redirects)

        self.area = ""
        self.continent = ""
        self.latitude = ""
        self.longitude = ""
        self.population = ""
        self.total_height = ""

        self.subtype = ""

    def set_entity_subtype(self, subtype):
        """
        Nastavuje podtyp geografické entity získaný z identifikace.

        Parametry:
        subtype - podtyp geografické entity (str)
        """
        if subtype in ("reliéf", "hora", "průsmyk", "pohoří", "sedlo"):
            self.subtype = "relief"
        elif subtype == "vodopád":
            self.subtype = "waterfall"
        elif subtype == "ostrov":
            self.subtype = "island"
        elif subtype == "poloostrov":
            self.subtype = "peninsula"
        elif subtype == "kontinent":
            self.subtype = "continent"
        else:
            self.subtype = "unknown"

        self.prefix += ":" + self.subtype

    @staticmethod
    def is_geo(title, content):
        """
        Na základě názvu a obsahu stránky určuje, zda stránka pojednává o geografické entitě, či nikoliv.

        Parametry:
        title - název stránky (str)
        content - obsah stránky (str)

        Návratové hodnoty:
        Dvojice hodnot (level, type); level určuje, zda stránka pojednává o geografické entitě, type určuje způsob, kterým byla stránka identifikována. (Tuple[int, str])
        """
        # kontrola šablon
        rexp = re.search(r"{{\s*Infobox\s*-\s*(reliéf|hora|průsmyk|vodopád|ostrov(?!ní)|kontinent)", content, re.I)
        if rexp:
            return 1, rexp.group(1).lower()

        # kontrola kategorií
        if re.search(r"\[\[\s*Kategorie:\s*Poloostrovy\s+(?:na|v)", content, re.I):
            return 2, "poloostrov"

        # kontrola závorek v názvu
        rexp = re.search(r"\((hora|pohoří|průsmyk|sedlo|vodopád|(?:polo)?ostrov|kontinent).*\)$", title, re.I)
        if rexp:
            return 3, rexp.group(1).lower()

        return 0, ""

    def get_data(self, content):
        """
        Extrahuje data o geografické entitě z obsahu stránky.

        Parametry:
        content - obsah stránky (str)
        """
        content = content.replace("&nbsp;", " ")
        content = re.sub(r"m\sn\.\s*", "metrů nad ", content)
# Šablona "světové dědictví" přináší do alternativních jmen spustu problémů - prozatím vyřešeno jinak v end_geo.del_redundant_text, protože jinak chybělo spoustu užitečných názvů
#        content = re.sub(r"(?sm)({{\s*Infobox\s*-\s*světové dědictví.*?)(?:|\s*název(?:[\s_]místním[\s_]jazykem)?\s*=(?!=)\s*)?(?:[^\n]*?\[[^\n]*?)(.*?^\s*}})", r"\1\2", content, re.I)
#        content = re.sub(r"(?sm)({{\s*Infobox\s*-\s*světové dědictví.*?)(?:|\s*jméno\s*=(?!=)\s*)?(?:[^\n]*?\[[^\n]*?)(.*?^\s*}})", r"\1\2", content, re.I)

        try:
            data = content.splitlines()
        except AttributeError:
            pass
        else:
            for ln in data:
                # aliasy
                rexp = re.search(r"(?:název(?:[\s_]místním[\s_]jazykem)?|jméno)\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_aliases(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázek - infobox
                rexp = re.search(r"(?:obrázek|mapa)\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázky - ostatní
                rexp = re.search(r"\[\[(?:Soubor|File):([^|]+?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg))(?:\|.*?)?\]\]", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(rexp.group(1))
                    continue

                # světadíl
                rexp = re.search(r"světadíl\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_continent(self.del_redundant_text(rexp.group(1)))
                    continue

                # zeměpisná šířka
                rexp = re.search(r"zeměpisná[\s_]šířka\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_latitude(self.del_redundant_text(rexp.group(1)))
                    continue

                # zeměpisná výška
                rexp = re.search(r"zeměpisná[\s_]délka\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_longitude(self.del_redundant_text(rexp.group(1)))
                    continue

                if self.subtype in ("continent", "island"):
                    # rozloha
                    rexp = re.search(r"rozloha\s*=(?!=)\s*(.*)", ln, re.I)
                    if rexp and rexp.group(1):
                        self.get_area(self.del_redundant_text(rexp.group(1)))
                        continue

                    # počet obyvatel
                    rexp = re.search(r"počet[\s_]obyvatel\s*=(?!=)\s*(.*)", ln, re.I)
                    if rexp and rexp.group(1):
                        self.get_population(self.del_redundant_text(rexp.group(1)))
                        continue

                if self.subtype == "waterfall":
                    rexp = re.search(r"celková[\s_]výška\s*=(?!=)\s*(.*)", ln, re.I)
                    if rexp and rexp.group(1):
                        self.get_total_height(self.del_redundant_text(rexp.group(1)))
                        continue

                # první věta
                abbrs = "".join((r"(?<!\s(?:tzv|at[pd]))", r"(?<!\s(?:apod|(?:ku|na|po)př|příp))", r"(?<!\s(?:[amt]j|fr))", r"(?<!\d)", r"(?<!nad m|ev\.\sč)"))
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
        Převádí rozlohu geografické entity do jednotného formátu.

        Parametry:
        area - rozloha geografické entity v kilometrech čtverečních (str)
        """
        is_ha = re.search(r"\d\s*(?:ha|hektar)", area, re.I)

        area = re.sub(r"\(.*?\)", "", area)
        area = re.sub(r"\[.*?\]", "", area)
        area = re.sub(r"<.*?>", "", area)
        area = re.sub(r"{{.*?}}", "", area).replace("{", "").replace("}", "")
        area = re.sub(r"(?<=\d)\s(?=\d)", "", area).strip()
        area = re.sub(r"(?<=\d)\.(?=\d)", ",", area)
        area = re.sub(r"^\D*(?=\d)", "", area)
        area = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", area)
        area = "" if not re.search(r"\d", area) else area

        if is_ha:  # je-li údaj uveden v hektarech, dojde k převodu na kilometry čtvereční
            try:
                area = str(float(area.replace(",", ".")) / 100).replace(".", ",")
            except ValueError:
                pass

        self.area = area

    def get_continent(self, continent):
        """
        Převádí světadíl, na kterém se geografická entita nachází, do jednotného formátu.

        Parametry:
        continent - světadíl, na kterém se geografická entita nachází (str)
        """
        continent = re.sub(r"\(.*?\)", "", continent)
        continent = re.sub(r"\[.*?\]", "", continent)
        continent = re.sub(r"<.*?>", "", continent)
        continent = re.sub(r"{{.*?}}", "", continent)
        continent = re.sub(r"\s+", " ", continent).strip()
        continent = re.sub(r", ?", "|", continent).replace("/", "|")

        self.continent = continent

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
        fs = re.sub(r"{{(?:cj|cizojazyčně|vjazyce\d?)\|\w+\|(.*?)}}", r"\1", fs)
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
        fs = re.sub(r"/.*?/", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"}}", "", fs) # Eliminate the end of a template
        fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",").replace(" .", ".")

        self.description = fs

    def get_latitude(self, latitude):
        """
        Převádí zeměpisnou šířku geografické entity do jednotného formátu.

        Parametry:
        latitude - zeměpisná šířka geografické entity (str)
        """
        latitude = re.sub(r"\(.*?\)", "", latitude)
        latitude = re.sub(r"\[.*?\]", "", latitude)
        latitude = re.sub(r"<.*?>", "", latitude)
        latitude = re.sub(r"{{.*?}}", "", latitude).replace("{", "").replace("}", "")
        latitude = re.sub(r"(?<=\d)\s(?=\d)", "", latitude).strip()
        latitude = re.sub(r"(?<=\d)\.(?=\d)", ",", latitude)
        latitude = re.sub(r"^[^\d-]*(?=\d)", "", latitude)
        latitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", latitude)
        latitude = "" if not re.search(r"\d", latitude) else latitude

        self.latitude = latitude

    def get_longitude(self, longitude):
        """
        Převádí zeměpisnou délku geografické entity do jednotného formátu.

        Parametry:
        longitude - zeměpisná délka geografické entity (str)
        """
        longitude = re.sub(r"\(.*?\)", "", longitude)
        longitude = re.sub(r"\[.*?\]", "", longitude)
        longitude = re.sub(r"<.*?>", "", longitude)
        longitude = re.sub(r"{{.*?}}", "", longitude).replace("{", "").replace("}", "")
        longitude = re.sub(r"(?<=\d)\s(?=\d)", "", longitude).strip()
        longitude = re.sub(r"(?<=\d)\.(?=\d)", ",", longitude)
        longitude = re.sub(r"^[^\d-]*(?=\d)", "", longitude)
        longitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", longitude)
        longitude = "" if not re.search(r"\d", longitude) else longitude

        self.longitude = longitude

    def get_population(self, population):
        """
        Převádí počet obyvatel, jenž žije na území geografické entity, do jednotného formátu.

        Parametry:
        population - počet obyvatel, jenž žije na území geografické entity (str)
        """

        coef = 1000000 if re.search(r"mil\.|mili[oó]n", population, re.I) else 1000 if re.search(r"tis\.|tis[ií]c", population, re.I) else 0

        population = re.sub(r"\(.*?\)", "", population)
        population = re.sub(r"\[.*?\]", "", population)
        population = re.sub(r"<.*?>", "", population)
        population = re.sub(r"{{.*?}}", "", population).replace("{", "").replace("}", "")
        population = re.sub(r"(?<=\d)[,.\s](?=\d)", "", population).strip()
        population = re.sub(r"^\D*(?=\d)", "", population)
        population = re.sub(r"^(\d+)\D.*$", r"\1", population)
        population = "0" if re.search(r"neobydlen|bez.+?obyvatel", population, re.I) else population  # pouze v tomto souboru
        population = "" if not re.search(r"\d", population) else population

        if coef and population:
            population = str(int(population) * coef)

        self.population = population

    def get_total_height(self, height):
        """
        Převádí celkovou výšku vodopádu do jednotného formátu.

        Parametry:
        height - ceková výška vodopádu (str)
        """
        height = re.sub(r"\(.*?\)", "", height)
        height = re.sub(r"\[.*?\]", "", height)
        height = re.sub(r"<.*?>", "", height)
        height = re.sub(r"{{.*?}}", "", height).replace("{", "").replace("}", "")
        height = re.sub(r"(?<=\d)\s(?=\d)", "", height).strip()
        height = re.sub(r"(?<=\d)\.(?=\d)", ",", height)
        height = re.sub(r"^\D*(?=\d)", "", height)
        height = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", height)
        height = "" if not re.search(r"\d", height) else height

        self.total_height = height

    def write_to_file(self):
        """
        Zapisuje údaje o geografické entitě do znalostní báze.
        """
        with open("kb_cs", "a", encoding="utf-8") as fl:
            fl.write(self.eid + "\t")
            fl.write(self.prefix + "\t")
            fl.write(self.title + "\t")
            fl.write(self.serialize_aliases() + "\t")
            fl.write(self.description + "\t")
            fl.write(self.original_title + "\t")
            fl.write(self.images + "\t")
            fl.write(self.link + ("\t" if self.subtype != "peninsula" else "\n"))

            if self.subtype in ("relief", "waterfall", "island"):
                fl.write(self.continent + "\t")

            if self.subtype != "peninsula":
                fl.write(self.latitude + "\t")
                fl.write(self.longitude + ("\t" if self.subtype != "relief" else "\n"))

            if self.subtype == "waterfall":
                fl.write(self.total_height + "\n")

            if self.subtype in ("island", "continent"):
                fl.write(self.area + "\t")
                fl.write(self.population + "\n")
