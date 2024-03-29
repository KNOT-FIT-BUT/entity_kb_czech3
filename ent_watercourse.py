#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autoři:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)

Popis souboru:
Soubor obsahuje třídu 'EntWatercourse', která uchovává údaje o vodních tocích.

Poznámky:
- typy vodních toků: bystřina|potok|říčka|řeka|veletok|průtok
"""

import re
from ent_core import EntCore


class EntWatercourse(EntCore):
    """
    Třída určená pro vodní toky.

    Instanční atributy:
    title - název vodního toku (str)
    prefix - prefix entity (str)
    eid - ID entity (str)
    link - odkaz na Wikipedii (str)
    aliases - alternativní pojmenování vodního toku (str)
    description - stručný popis vodního toku (str)
    images - absolutní cesty k obrázkům Wikimedia Commons (str)

    area - plocha povodí vodního toku v kilometrech čtverečních (str)
    continent - světadíl, kterým vodní tok protéká (str)
    length - délka vodního toku v kilometrech (str)
    source_loc - umístění pramene vodního toku (str)
    streamflow - průtok vodního toku (str)
    """

    def __init__(self, title, prefix, link, redirects, langmap):
        """
        Inicializuje třídu 'EntWatercourse'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntWatercourse, self).__init__(title, prefix, link, redirects, langmap)

        self.area = ""
        self.continent = ""
        self.length = ""
        self.source_loc = ""
        self.streamflow = ""

        self.re_infobox_kw_img = r"(?:obrázek|mapa)"

        self.get_wiki_api_location(title)

    @staticmethod
    def is_watercourse(title, content):
        """
        Na základě názvu a obsahu stránky určuje, zda stránka pojednává o vodním toku, či nikoliv.

        Parametry:
        title - název stránky (str)
        content - obsah stránky (str)

        Návratové hodnoty:
        Dvojice hodnot (level, type); level určuje, zda stránka pojednává o vodním toku, type určuje způsob, kterým byla stránka identifikována. (Tuple[int, str])
        """
        # kontrola šablon
        if re.search(r"{{\s*Infobox\s*-\s*vodní\s+tok", content, re.I):
            return 1, "Infobox 'vodní tok'"

        # kontrola kategorií
        for kw in (
            "Potoky",
            "Řeky",
        ):  # žádná další klíčová slova nejsou vhodná, zejména ne "Říčky"
            if re.search(
                r"\[\[\s*Kategorie:\s*" + kw + r"\s+(?:na|ve?)\s+.+?\]\]", content, re.I
            ):
                return 2, "Kategorie '" + kw + "'"

        # kontrola názvu
        rexp = re.search(r"\((?:bystřina|potok|říčka|řeka|veletok|průtok)\)$", title)
        if rexp:
            return 3, "Název '" + rexp.group(0) + "'"

        return 0, ""

    def data_preprocess(self, content):
        """
        Předzpracování dat o vodním toku z obsahu stránky.

        Parametry:
        content - obsah stránky (str)
        """
        content = content.replace("&nbsp;", " ")
        content = re.sub(r"m\sn\.\s*", "metrů nad ", content)

    def line_process_infobox(self, ln, is_infobox_block):
        # aliasy
        rexp = re.search(r"řeka\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox.update(
                self.get_aliases(self.del_redundant_text(rexp.group(1)))
            )
            if is_infobox_block == True:
                return

        # zeměpisná šířka
        rexp = re.search(r"zeměpisná[\s_]šířka\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_latitude(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # zeměpisná výška
        rexp = re.search(r"zeměpisná[\s_]délka\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_longitude(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # délka toku
        rexp = re.search(r"(?<!zeměpisná[\s_])délka\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_length(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # plocha
        rexp = re.search(r"plocha\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_area(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # světadíl
        rexp = re.search(r"světadíl\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_continent(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # průtok
        rexp = re.search(r"průtok\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_streamflow(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # pramen
        rexp = re.search(r"pramen\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_source_loc(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

    def line_process_1st_sentence(self, ln):
        abbrs = "".join(
            (
                r"(?<!\s(?:tzv|at[pd]))",
                r"(?<!\s(?:apod|(?:ku|na|po)př|příp))",
                r"(?<!\s(?:[amt]j|fr))",
                r"(?<!\d)",
                r"(?<!nad m)",
            )
        )
        rexp = re.search(
            r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|nacház(?:í|ejí)|patř(?:í|il)|stal|rozprostír|lež(?:í|el)|pramen(?:í|il)).*?"
            + abbrs
            + "\.(?![^[]*?\]\])",
            ln,
        )
        if rexp:
            if not self.description:
                self.get_first_sentence(self.del_redundant_text(rexp.group(0), ", "))
                tmp_first_sentence = rexp.group(0)

                # extrakce alternativních pojmenování z první věty
                fs_aliases_lang_links = []
                for link_lang_alias in re.findall(
                    r"\[\[(?:[^\[]* )?([^\[\] |]+)(?:\|(?:[^\]]* )?([^\] ]+))?\]\]\s*('{3}.+?'{3})",
                    tmp_first_sentence,
                    flags=re.I,
                ):
                    for i_group in [0, 1]:
                        if (
                            link_lang_alias[i_group]
                            and link_lang_alias[i_group] in self.langmap
                        ):
                            fs_aliases_lang_links.append(
                                "{{{{Vjazyce|{}}}}} {}".format(
                                    self.langmap[link_lang_alias[i_group]],
                                    link_lang_alias[2],
                                )
                            )
                            tmp_first_sentence = tmp_first_sentence.replace(
                                link_lang_alias[2], ""
                            )
                            break
                fs_aliases = re.findall(
                    r"((?:{{(?:Cj|Cizojazyčně|Vjazyce2?)[^}]+}}\s+)?(?<!\]\]\s)'{3}.+?'{3})",
                    tmp_first_sentence,
                    flags=re.I,
                )
                fs_aliases += fs_aliases_lang_links
                if fs_aliases:
                    for fs_alias in fs_aliases:
                        self.aliases.update(
                            self.get_aliases(
                                self.del_redundant_text(fs_alias).strip("'")
                            )
                        )

    def custom_transform_alias(self, alias):
        """
        Vlastní transformace aliasu.

        Parametry:
        alias - alternativní pojmenování entity (str)
        """

        return self.transform_geo_alias(alias)

    def get_area(self, area):
        """
        Převádí plochu vodního toku do jednotného formátu.

        Parametry:
        area - plocha vodního toku v kilometrech čtverečních (str)
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

    def get_continent(self, continent):
        """
        Převádí světadíl, kterým vodní tok protéká, do jednotného formátu.

        Parametry:
        continent - světadíl, kterým vodní tok protéká (str)
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
        # TODO: refactorize
        fs = re.sub(r"\(.*?\)", "", fs)
        fs = re.sub(r"\[.*?\]", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(
            r"{{(?:cj|cizojazyčně|vjazyce\d?)\|\w+\|(.*?)}}", r"\1", fs, flags=re.I
        )
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
        fs = re.sub(r"/.*?/", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"^\s*}}", "", fs)  # Eliminate the end of a template
        fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",").replace(" .", ".")

        self.description = fs

    def get_length(self, length):
        """
        Převádí délku vodního toku do jenotného formátu.

        Parametry:
        length - délka vodního toku v kilometrech (str)
        """
        length = re.sub(r"\(.*?\)", "", length)
        length = re.sub(r"\[.*?\]", "", length)
        length = re.sub(r"<.*?>", "", length)
        length = re.sub(r"{{.*?}}", "", length).replace("{", "").replace("}", "")
        length = re.sub(r"(?<=\d)\s(?=\d)", "", length).strip()
        length = re.sub(r"(?<=\d)\.(?=\d)", ",", length)
        length = re.sub(r"^\D*(?=\d)", "", length)
        length = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", length)
        length = "" if not re.search(r"\d", length) else length

        self.length = length

    def get_source_loc(self, source_loc):
        """
        Převádí umístění pramene vodního toku do jednotného formátu.

        Parametry:
        source_loc - místo, kde vodní tok pramení (str)
        """
        source_loc = re.sub(r"\[.*?\]", "", source_loc)
        source_loc = re.sub(r"<.*?>", "", source_loc)
        source_loc = (
            re.sub(r"{{.*?}}", "", source_loc).replace("()", "").strip().strip(",")
        )
        source_loc = re.sub(r"\s+", " ", source_loc).strip()

        self.source_loc = source_loc

    def get_streamflow(self, streamflow):
        """
        Převádí průtok vodního toku do jednotného formátu.

        Parametry:
        streamflow - průtok vodního toku v metrech krychlových za sekundu (str)
        """
        streamflow = re.sub(r"\(.*?\)", "", streamflow)
        streamflow = re.sub(r"\[.*?\]", "", streamflow)
        streamflow = re.sub(r"<.*?>", "", streamflow)
        streamflow = (
            re.sub(r"{{.*?}}", "", streamflow).replace("{", "").replace("}", "")
        )
        streamflow = re.sub(r"(?<=\d)\s(?=\d)", "", streamflow).strip()
        streamflow = re.sub(r"(?<=\d)\.(?=\d)", ",", streamflow)
        streamflow = re.sub(r"^\D*(?=\d)", "", streamflow)
        streamflow = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", streamflow)
        streamflow = "" if not re.search(r"\d", streamflow) else streamflow

        self.streamflow = streamflow

    def serialize(self):
        """
        Serializuje údaje o vodním toku.
        """
        return "\t".join(
            [
                self.eid,
                self.prefix,
                self.title,
                self.serialize_aliases(),
                "|".join(self.redirects),
                self.description,
                self.original_title,
                self.images,
                self.link,
                self.continent,
                self.latitude,
                self.longitude,
                self.length,
                self.area,
                self.streamflow,
                self.source_loc,
            ]
        )
