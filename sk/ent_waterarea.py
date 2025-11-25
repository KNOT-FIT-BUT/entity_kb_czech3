#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autori:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)
    Samuel Križan (xkriza06)

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
        super(EntWaterArea, self).__init__(
            title, prefix, link, redirects, langmap)

        self.area = ""
        self.continent = ""

        self.re_infobox_kw_img = r"(?:obrázok|mapa)"

        self.get_wiki_api_data()

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
        rexp = re.search(
            r"{{\s*Infobox\s*(vodná\s+plocha|more)", content, re.I)
        if rexp:
            return 1, "Infobox " + "'" + rexp.group(1) + "'"

        rexp = re.search(
            r"{{\s*Geobox\s*\|\s*(Lake|Sea|Reservoir|Water|Ocean)", content, re.I)
        if rexp:
            return 1, "Infobox " + "'" + rexp.group(1) + "'"

        if re.search(r"{{\s*oceány\s*}}", content, re.I):
            return 1, "Infobox 'oceány'"

        # kontrola kategorií
        for kw in ("Rybníky", "Jazerá", "Riečne jazerá", "Vodné diela", "Zálivy", "Rieky", "Potoky"):
            if re.search(
                r"\[\[\s*Kategória:\s*" + kw +
                    r"\s+(?:na|v?)\s+.+?\]\]", content, re.I
            ):
                return 2, "Kategória '" + kw + "'"

        # kontrola názvu
        rexp = re.search(
            r"\((?:rybník|jazero|more|oceán|tôňa|vodné dielo)\)$", title)
        if rexp:
            return 3, "Názov '" + rexp.group(0) + "'"

        return 0, ""

    def data_preprocess(self, content):
        """
        Předzpracování dat o vodní ploše.

        Parametry:
        content - obsah stránky (str)
        """
        content = content.replace("&nbsp;", " ")
        content = re.sub(r"m\sn\.\s*", "metrov nad ", content)

    def line_process_infobox(self, ln, is_infobox_block):
        # aliasy
        rexp = re.search(
            r"názov\s*=(?!=)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox.update(
                self.get_aliases(self.del_redundant_text(rexp.group(1)))
            )
            if is_infobox_block == True:
                return

        # světadíl
        rexp = re.search(
            r"svetadiel\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.get_continent(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # zeměpisná šířka
        if self.latitude == "":
            rexp = re.search(
                r"(?:zemepisná[\s_]šírka|\s+lat_d)\s*=(?!=)\s*([^\|]*)", ln, re.I)
            if rexp and rexp.group(1):
                self.get_latitude(self.del_redundant_text(rexp.group(1)))
                if is_infobox_block == True:
                    return

        # zeměpisná dĺžka
        if self.longitude == "":
            rexp = re.search(
                r"(?:zemepisná[\s_]dĺžka|\s+long_d)\s*=(?!=)\s*([^\|]*)", ln, re.I)
            if rexp and rexp.group(1):
                self.get_longitude(self.del_redundant_text(rexp.group(1)))
                if is_infobox_block == True:
                    return

        # rozloha
        rexp = re.search(
            r"(?:rozloha|area)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.get_area(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

    def line_process_1st_sentence(self, ln):
        # první věta
        abbrs = "".join(
            (
                r"(?<!\s(?:tzv|atď))",
                r"(?<!\s(?:apod|(?:napr)))",
                r"(?<!\s(?:[amt]j|fr))",
                r"(?<!\d)",
                r"(?<!nad m|ev\.\sč)",
            )
        )
        rexp = re.search(
            r".*?'''.+?'''.*?\s(?:bol[aiy]?|je|sú|nachádz(?:a|ajú)|patr(?:í|il|ila|ilo)|stal|rozprestier(?:a|al)|lež(?:í|al)).*?"
            + abbrs
            + "\.(?![^[]*?\]\])",
            ln,
        )
        if rexp:
            if not self.description:
                self.get_first_sentence(
                    self.del_redundant_text(rexp.group(0), ", "))
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
                                "{{{{V jazyku|{}}}}} {}".format(
                                    self.langmap[link_lang_alias[i_group]],
                                    link_lang_alias[2],
                                )
                            )
                            tmp_first_sentence = tmp_first_sentence.replace(
                                link_lang_alias[2], ""
                            )
                            break
                fs_aliases = re.findall(
                    r"((?:{{(?:v jazyku|lang|audio|cj|jazyk|vjz|cudzojazyčne|cjz)[^}]+}}\s+)?(?<!\]\]\s)'{3}.+?'{3})",
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
        Převádí rozlohu vodní plochy do jednotného formátu.

        Parametry:
        area - rozloha vodní plochy v kilometrech čtverečních (str)
        """
        is_ha = re.search(r"\d\s*(?:ha|hektár)", area, re.I)

        area = re.sub(r"\(.*?\)", "", area)
        area = re.sub(r"\[.*?\]", "", area)
        area = re.sub(r"<.*?>", "", area)
        area = re.sub(r"{{.*?}}", "", area).replace("{", "").replace("}", "")
        area = re.sub(r"(?<=\d)\s(?=\d)", "", area).strip()
        area = re.sub(r"(?<=\d)\.(?=\d)", ",", area)
        area = re.sub(r"^\D*(?=\d)", "", area)
        area = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", area)
        area = "" if not re.search(r"\d", area) else area

        if (
            is_ha
        ):  # je-li údaj uveden v hektarech, dojde k převodu na kilometry čtvereční
            try:
                area = str(float(area.replace(",", ".")) /
                           100).replace(".", ",")
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
        # TODO: refactorize
        fs = re.sub(r"\(.*?\)", "", fs)
        fs = re.sub(r"\[.*?\]", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(
            r"{{(?:v jazyku|lang|audio|cj|jazyk|vjz|cudzojazyčne|cjz)\|\w+\|(.*?)}}", r"\1", fs, flags=re.I
        )
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
        fs = re.sub(r"/.*?/", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"^\s*}}", "", fs)  # Eliminate the end of a template
        fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,",
                                                      ",").replace(" .", ".")
        fs = re.sub(r"\|(?:.+?)(?=\|[^\|]*\=)", "", fs)
        fs = re.sub(r"\|[^=]*=", "", fs)
        self.description = fs

    def serialize(self):
        """
        Serializuje údaje o vodní ploše.
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
                self.wikidata_id,
                self.continent,
                self.latitude,
                self.longitude,
                self.area
            ]
        )
