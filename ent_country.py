#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje třídu 'EntCountry', která uchovává údaje o státech.

Poznámky:
Infobox - stát
Infobox - region
Infobox stát USA
"""

import re
from ent_core import EntCore


class EntCountry(EntCore):
    """
    Třída určená pro státy.

    Instanční atributy:
    title - název státu (str)
    prefix - prefix entity (str)
    eid - ID entity (str)
    link - odkaz na Wikipedii (str)
    aliases - alternativní pojmenování státu (str)
    description - stručný popis státu (str)
    images - absolutní cesty k obrázkům Wikimedia Commons (str)

    area - rozloha státu v kilometrech čtverečních (str)
    population - počet obyvatel státu (str)
    """

    def __init__(self, title, prefix, link, redirects):
        """
        Inicializuje třídu 'EntCountry'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntCountry, self).__init__(title, prefix, link, redirects)

        self.area = ""
        self.population = ""

    @staticmethod
    def is_country(content):
        """
        Na základě obsahu stránky určuje, zda stránka pojednává o státu, či nikoliv.

        Parametry:
        content - obsah stránky (str)

        Návratové hodnoty:
        1 v případě, že stránka pojednává o státu, jinak 0. (int)
        """
        # kontrola kategorií - začátek
        # státy podle kontinentů
        rexp_format = "Státy\s+(?:Afriky|Asie|Austrálie\s+a\s+Oceánie|Evropy|(?:Severní|Jižní)\s+Ameriky)"
        if re.search(r"\[\[\s*Kategorie:\s*" + rexp_format + "\s*\]\]", content, re.I):
            return 1

        # státy podle mezinárodních organizací
        if re.search(r"\[\[\s*Kategorie:\s*Státy\s+(?:NATO|EU|Commonwealthu)\s*\]\]", content, re.I):
            return 1

        # neuznané či jen částečně uznané státy
        if re.search(r"\[\[\s*Kategorie:\s*Státy\s+s\s+žádným\s+nebo\s+částečným\s+mezinárodním\s+uznáním\s*\]\]", content, re.I):
            return 1
        # kontrola kategorií - konec

        return 0

    def get_data(self, content):
        """
        Extrahuje data o státu z obsahu stránky.

        Parametry:
        content - obsah stránky (str)
        """
        # prefix - zaniklé státy
        if re.search(r"\[\[\s*Kategorie:\s*(?:Krátce\s+existující\s+státy|Zaniklé\s+(?:státy|monarchie))", content, re.I):
            self.prefix = "country:former"

        try:
            data = content.splitlines()
        except AttributeError:
            pass
        else:
            for ln in data:
                # aliases - czech name is preferable
                rexp = re.search(r"název[\s_]česky\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_aliases(self.del_redundant_text(rexp.group(1)), True)
                    continue

                # aliases - common name may contain name in local language
                rexp = re.search(r"název\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_aliases(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázek - infobox
                rexp = re.search(r"(?:vlajka|znak|mapa[\s_]umístění)\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(self.del_redundant_text(rexp.group(1)))
                    continue

                # obrázky - ostatní
                rexp = re.search(r"\[\[(?:Soubor|File):([^|]+?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg))(?:\|.*?)?\]\]", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(rexp.group(1))
                    continue

                # počet obyvatel
                rexp = re.search(r"obyvatel\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_population(self.del_redundant_text(rexp.group(1)))
                    continue

                # rozloha
                rexp = re.search(r"(?:rozloha|výměra)\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_area(self.del_redundant_text(rexp.group(1)))
                    continue

                # první věta
                abbrs = "".join((r"(?<!\s(?:tzv|at[dp]))", r"(?<!\s(?:apod|(?:ku|na|po)př|příp))", r"(?<!\s(?:[amt]j|fr))", r"(?<!\d)"))
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
        Převádí rozlohu státu do jednotného formátu.

        Parametry:
        area - rozloha státu (str)
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

    def get_first_sentence(self, fs):
        """
        Převádí první větu stránky do jednotného formátu a získává z ní popis.

        Parametry:
        fs - první věta stránky (str)
        """
        fs = re.sub(r"{{(?:vjazyce2|cizojazyčně|audio|cj|jazyk)\|.*?\|(.+?)}}", r"", fs, flags=re.I)
        fs = re.sub(r"{{IPA\d?\|(.+?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{výslovnost\|(.+?)\|.*?}}", r"", fs, flags=re.I)
        fs = re.sub(r"{{čínsky(.+?)}}", lambda x: re.sub("(?:znaky|pchin-jin|tradiční|zjednodušené|pinyin)"
                                                         "\s*=\s*(.*?)(?:\||}})", r"\1 ", x.group(1), flags=re.I),
                    fs, flags=re.I)
        fs = re.sub(r"{{malé\|(.*?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(r"\(.*?\)", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r" ([,.])", r"\1", fs)
        fs = fs.replace("''", "").replace(")", "").replace("|group=pozn.}}", "")

        self.description = fs

    def get_population(self, population):
        """
        Převádí počet obyvatel státu do jednotného formátu.

        Parametry:
        population - počet obyvatel státu (str)
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
        Zapisuje údaje o státu do znalostní báze.
        """
        with open("kb_cs", "a", encoding="utf-8") as fl:
            fl.write(self.eid + "\t")
            fl.write(self.prefix + "\t")
            fl.write(self.title + "\t")
            fl.write(self.serialize_aliases() + "\t")
            fl.write(self.description + "\t")
            fl.write(self.images + "\t")
            fl.write(self.link + "\t")
            fl.write(self.area + "\t")
            fl.write(self.population + "\n")
