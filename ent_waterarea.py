#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autoři:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)

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

    def __init__(self, title, prefix, link, redirects, langmap):
        """
        Inicializuje třídu 'EntWaterArea'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntWaterArea, self).__init__(title, prefix, link, redirects, langmap)

        self.area = ""
        self.continent = ""

        self.re_infobox_kw_img = r"(?:obrázek|mapa)"

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


    def data_preprocess(self, content):
        """
        Předzpracování dat o vodní ploše.

        Parametry:
        content - obsah stránky (str)
        """
        content = content.replace("&nbsp;", " ")
        content = re.sub(r"m\sn\.\s*", "metrů nad ", content)


    def line_process_infobox(self, ln, is_infobox_block):
        # aliasy
        rexp = re.search(r"název\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_aliases(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # světadíl
        rexp = re.search(r"světadíl\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_continent(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # rozloha
        rexp = re.search(r"rozloha\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_area(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

    def line_process_1st_sentence(self, ln):
        # první věta
        abbrs = "".join((r"(?<!\s(?:tzv|at[pd]))", r"(?<!\s(?:apod|(?:ku|na|po)př|příp))", r"(?<!\s(?:[amt]j|fr))", r"(?<!\d)", r"(?<!nad m|ev\.\sč)"))
        rexp = re.search(r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|nacház(?:í|ejí)|patř(?:í|il)|stal|rozprostír|lež(?:í|el)).*?" + abbrs + "\.(?![^[]*?\]\])", ln)
        if rexp:
            if not self.description:
                self.get_first_sentence(self.del_redundant_text(rexp.group(0), ", "))
                tmp_first_sentence = rexp.group(0)

                # extrakce alternativních pojmenování z první věty
                fs_aliases_lang_links = []
                for link_lang_alias in re.findall(r"\[\[(?:.* )?([^ |]+)(?:\|(?:.* )?([^ ]+))?\]\]\s*('{3}.+?'{3})", tmp_first_sentence, flags = re.I):
                    for i_group in [0,1]:
                        if link_lang_alias[i_group] and link_lang_alias[i_group] in self.langmap:
                            fs_aliases_lang_links.append("{{{{Vjazyce|{}}}}} {}".format(self.langmap[link_lang_alias[i_group]], link_lang_alias[2]))
                            tmp_first_sentence = tmp_first_sentence.replace(link_lang_alias[2], '')
                            break
                fs_aliases = re.findall(r"((?:{{(?:Cj|Cizojazyčně|Vjazyce2?)[^}]+}}\s+)?(?<!\]\]\s)'{3}.+?'{3})", tmp_first_sentence, flags = re.I)
                fs_aliases += fs_aliases_lang_links
                if fs_aliases:
                    for fs_alias in fs_aliases:
                        self.get_aliases(self.del_redundant_text(fs_alias).strip("'"))


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
        #TODO: refactorize
        fs = re.sub(r"\(.*?\)", "", fs)
        fs = re.sub(r"\[.*?\]", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(r"{{(?:cj|cizojazyčně|vjazyce\d?)\|\w+\|(.*?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
        fs = re.sub(r"/.*?/", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"^\s*}}", "", fs) # Eliminate the end of a template
        fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",").replace(" .", ".")

        self.description = fs

    def serialize(self):
        """
        Serializuje údaje o vodní ploše.
        """
        return "\t".join([
                   self.eid,
                   self.prefix,
                   self.title,
                   self.serialize_aliases(),
                   '|'.join(self.redirects),
                   self.description,
                   self.original_title,
                   self.images,
                   self.link,
                   self.continent,
                   self.area
               ])
