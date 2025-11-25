#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autori:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)
    Samuel Križan (xkriza06)

Popis souboru:
Soubor obsahuje třídu 'EntGeo', která uchovává údaje o geografických entitách.

TODO: odstavec "Název"
"""

import re
import sys
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

    def __init__(self, title, prefix, link, redirects, langmap):
        """
        Inicializuje třídu 'EntGeo'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntGeo, self).__init__(title, prefix, link, redirects, langmap)

        self.area = ""
        self.continent = ""
        self.latitude = ""
        self.longitude = ""
        self.population = ""
        self.total_height = ""

        self.subtype = ""

        self.re_infobox_kw_img = r"(?:obrázok|mapa)"

        self.get_wiki_api_data()

    def set_entity_subtype(self, subtype):
        """
        Nastavuje podtyp geografické entity získaný z identifikace.

        Parametry:
        subtype - podtyp geografické entity (str)
        """
        if subtype in ("reliéf", "vrch", "priesmyk", "pohorie", "sedlo", "mountain", "pass", "mountain range", "volcano", "caldera", "valley"):
            self.subtype = "relief"
        elif subtype in ("vodopád", "waterfall"):
            self.subtype = "waterfall"
        elif subtype in ("ostrov", "island"):
            self.subtype = "island"
        elif subtype in ("polostrov", "peninsula"):
            self.subtype = "peninsula"
        elif subtype in ("kontinent", "continent"):
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
        rexp = re.search(
            r"{{\s*Infobox\s*(reliéf|vrch|priesmyk|pohorie|vodopád|ostrov(?!ný)|kontinent)",
            content,
            re.I,
        )
        if not rexp:
            rexp = re.search(
                r"{{\s*Geobox\s*\|\s*(Mountain|peninsula|Pass|Mountain\sRange|Waterfall|Island|Continent|Volcano|Caldera|Valley)",
                content,
                re.I,
            )
        if rexp:
            return 1, rexp.group(1).lower()

        # kontrola kategorií
        if re.search(r"\[\[\s*Kategória:\s*Polostrovy\s*\w", content, re.I):
            return 2, "polostrov"
        if re.search(r"\[\[\s*Kategória:\s*(Ostrovy|Súostrovia)\s*\w", content, re.I):
            return 2, "ostrov"
        if re.search(r"\[\[\s*Kategória:\s*(Pohoria|Vrchy|Kaňony|Doliny|Nížiny|Priepasti|Sopky|Púšte)\s*\w", content, re.I):
            return 2, "reliéf"
        if re.search(r"\[\[\s*Kategória:\s*Vodopády\s*\w", content, re.I):
            return 2, "vodopád"

        # kontrola závorek v názvu
        rexp = re.search(
            r"\((hora|pohorie|vrch|priesmyk|sedlo|vodopád|(?:pol)?ostrov|kontinent).*\)$",
            title,
            re.I,
        )
        if rexp:
            return 3, rexp.group(1).lower()

        return 0, ""

    def data_preprocess(self, content):
        """
        Předzpracování dat o geografické entitě.

        Parametry:
        content - obsah stránky (str)
        """
        content = content.replace("&nbsp;", " ")
        content = re.sub(r"m\sn\.\s*", "metrov nad ", content)

    def line_process_infobox(self, ln, is_infobox_block):
        # aliasy
        rexp = re.search(
            r"(?:názov|meno|name)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox.update(
                self.get_aliases(self.del_redundant_text(rexp.group(1)))
            )
            if is_infobox_block == True:
                return

        rexp = re.search(
            r"(?:názov[\s_]miestnym[\s_]jazykom|native_name)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox_orig.update(
                self.get_aliases(self.del_redundant_text(rexp.group(1)))
            )
            if not len(self.aliases) and not len(self.aliases_infobox):
                self.first_alias = None

            if is_infobox_block == True:
                return

        rexp = re.search(
            r"(?:other_name|nickname|official_name)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox_orig.update(
                self.get_aliases(self.del_redundant_text(rexp.group(1)))
            )
            if not len(self.aliases) and not len(self.aliases_infobox):
                self.first_alias = None

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

        if self.subtype in ("continent", "island"):
            # rozloha
            rexp = re.search(
                r"(?:Rozloha|area|area_land)\s*=(?!=)\s*(?:{{km2\|)?((?:\d|,|\s)+)", ln, re.I)
            if rexp and rexp.group(1):
                self.get_area(self.del_redundant_text(rexp.group(1)))
                if is_infobox_block == True:
                    return

            # počet obyvatel
            rexp = re.search(
                r"(?:Obyvatelia|population|Sčítanie\spočtu\sobyvateľov)\s*=(?!=)\s*(.*)", ln, re.I)
            if rexp and rexp.group(1):
                self.get_population(self.del_redundant_text(rexp.group(1)))
                if is_infobox_block == True:
                    return

        if self.subtype == "waterfall":
            rexp = re.search(
                r"(?:celková[\s_]výška|elevation)\s*=(?!=)\s*(.*)", ln, re.I)
            if rexp and rexp.group(1):
                self.get_total_height(self.del_redundant_text(rexp.group(1)))
                if is_infobox_block == True:
                    return

    def line_process_1st_sentence(self, ln):
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
            r".*?'''.+?'''.*?\s(?:bol[aiy]?|je|sú|nachádz(?:a|ajú)|patr(?:í|il)|stal|rozprestier(?:a|al)|lež(?:í|al)).*?(?:"
            + abbrs
            + "\.(?!(?:[^[]*?\]\]|\s*[a-z]))|\.$)",
            ln,
        )
        if rexp:
            if not self.description:
                self.get_first_sentence(
                    self.del_redundant_text(rexp.group(0), ", "))

                tmp_first_sentence = rexp.group(0)
                fs_aliases_lang_links = []
                # extrakce alternativních pojmenování z první věty
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
        Převádí rozlohu geografické entity do jednotného formátu.

        Parametry:
        area - rozloha geografické entity v kilometrech čtverečních (str)
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

    def get_population(self, population):
        """
        Převádí počet obyvatel, jenž žije na území geografické entity, do jednotného formátu.

        Parametry:
        population - počet obyvatel, jenž žije na území geografické entity (str)
        """

        coef = (
            1000000
            if re.search(r"mil\.|mili[oó]n", population, re.I)
            else 1000
            if re.search(r"tis\.|tis[ií]c", population, re.I)
            else 0
        )

        population = re.sub(r"\(.*?\)", "", population)
        population = re.sub(r"\[.*?\]", "", population)
        population = re.sub(r"<.*?>", "", population)
        population = (
            re.sub(r"{{.*?}}", "", population).replace("{", "").replace("}", "")
        )
        population = re.sub(r"(?<=\d)[,.\s](?=\d)", "", population).strip()
        population = re.sub(r"^\D*(?=\d)", "", population)
        population = re.sub(r"^(\d+)\D.*$", r"\1", population)
        population = (
            "0"
            if re.search(r"neobývaný|bez.+?obyvateľov", population, re.I)
            else population
        )  # pouze v tomto souboru
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
        height = re.sub(
            r"{{.*?}}", "", height).replace("{", "").replace("}", "")
        height = re.sub(r"(?<=\d)\s(?=\d)", "", height).strip()
        height = re.sub(r"(?<=\d)\.(?=\d)", ",", height)
        height = re.sub(r"^\D*(?=\d)", "", height)
        height = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", height)
        height = "" if not re.search(r"\d", height) else height

        self.total_height = height

    def serialize(self):
        """
        Serializuje údaje o geografické entitě.
        """
        cols = [
            self.eid,
            self.prefix,
            self.title,
            self.serialize_aliases(),
            "|".join(self.redirects),
            self.description,
            self.original_title,
            self.images,
            self.link,
            self.wikidata_id
        ]

        if self.subtype in ("relief", "waterfall", "island"):
            cols.extend([self.continent])

        cols.extend([self.latitude, self.longitude])

        if self.subtype == "waterfall":
            cols.extend([self.total_height])

        if self.subtype in ("island", "continent"):
            cols.extend([self.area, self.population])

        return "\t".join(cols)
