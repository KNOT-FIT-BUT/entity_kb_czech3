#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje třídu 'EntWaterArea', která uchovává údaje o vodních plochách.
"""

import re
from ent_core import EntCore


class EntWaterArea(EntCore):
    """
    Třída určená pro vodní plochy.

    Instanční atributy:
    title - název vodní plochy (str)
    prefix - prefix entity (str)
    eid - ID entity (str)
    link - odkaz na Wikipedii (str)
    aliases - alternativní pojmenování vodní plochy (str)
    description - stručný popis vodní plochy (str)
    images - absolutní cesty k obrázkům Wikimedia Commons (str)

    area - rozloha vodní plochy v kilometrech čtverečních (str)
    continent - světadíl, na kterém se vodní plocha nachází (str)
    """

    def __init__(self, title, prefix, link, redirects):
        """
        Inicializuje třídu 'EntWaterArea'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntWaterArea, self).__init__(title, prefix, link, redirects)

        self.area = ""
        self.continent = ""

    @staticmethod
    def is_water_area(title, content):
        """
        Na základě názvu a obsahu stránky určuje, zda stránka pojednává o vodní ploše, či nikoliv.

        Parametry:
        title - název stránky (str)
        content - obsah stránky (str)

        Návratové hodnoty:
        Dvojice hodnot (level, type); level určuje, zda stránka pojednává o vodní ploše, type určuje způsob, kterým byla stránka identifikována. (Tuple[int, str])
        """
        # kontrola šablon
        rexp = re.search(r"{{\s*Infobox\s*-\s*(vodní\s+plocha|moře)", content, re.I)
        if rexp:
            return 1, "Infobox " + "'" + rexp.group(1) + "'"

        if re.search(r"{{\s*oceány\s*}}", content, re.I):
            return 1, "Infobox 'oceány'"

        # kontrola kategorií
        for kw in ("Rybníky", "Jezera", "Říční jezera"):
            if re.search(r"\[\[\s*Kategorie:\s*" + kw + r"\s+(?:na|ve?)\s+.+?\]\]", content, re.I):
                return 2, "Kategorie '" + kw + "'"

        # kontrola názvu
        rexp = re.search(r"\((?:rybník|jezero|moře|oceán|tůň)\)$", title)
        if rexp:
            return 3, "Název '" + rexp.group(0) + "'"

        return 0, ""

    def get_data(self, content):
        """
        Extrahuje data o vodní ploše z obsahu stránky.

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
                rexp = re.search(r"název\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_aliases(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázek - infobox
                rexp = re.search(r"(?:obrázek|mapa)\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázky - ostatní
                rexp = re.search(r"\[\[(?:Soubor|File):([^|]+?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg))(?:\|.*?)?\]\]",
                                 ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(rexp.group(1))
                    continue

                # světadíl
                rexp = re.search(r"světadíl\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_continent(self.del_redundant_text(rexp.group(1)))
                    continue

                # rozloha
                rexp = re.search(r"rozloha\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_area(self.del_redundant_text(rexp.group(1)))
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
        Převádí rozlohu vodní plochy do jednotného formátu.

        Parametry:
        area - rozloha vodní plochy v kilometrech čtverečních (str)
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
        Převádí světadíl, na kterém se vodní plocha nachází, do jednotného formátu.

        Parametry:
        continent - světadíl, na kterém se vodní plocha nachází (str)
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
        fs = re.sub(r"\(.*?\)", "", fs)
        fs = re.sub(r"\[.*?\]", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(r"{{(?:cizojazyčně|vjazyce\d?)\|\w+\|(.*?)}}", r"\1", fs)
        fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
        fs = re.sub(r"/.*?/", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",").replace(" .", ".")

        self.description = fs

    def write_to_file(self):
        """
        Zapisuje údaje o vodní ploše do znalostní báze.
        """
        with open("kb_cs", "a", encoding="utf-8") as fl:
            fl.write(self.eid + "\t")
            fl.write(self.prefix + "\t")
            fl.write(self.title + "\t")
            fl.write(self.serialize_aliases() + "\t")
            fl.write(self.description + "\t")
            fl.write(self.images + "\t")
            fl.write(self.link + "\t")
            fl.write(self.continent + "\t")
            fl.write(self.area + "\n")
