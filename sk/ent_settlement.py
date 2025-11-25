#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autori:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)
    Samuel Križan (xkriza06)

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
import sys
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

    def __init__(self, title, prefix, link, redirects, langmap):
        """
        Inicializuje třídu 'EntSettlement'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """
        super(EntSettlement, self).__init__(
            title, prefix, link, redirects, langmap)

        self.area = ""
        self.country = ""
        self.population = ""

        self.re_infobox_kw_img = r"(?:obrázok|vlajka|znak|logo)"

        self.get_wiki_api_data()

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
        id_level, id_type = cls._contains_settlement_infoboxes(
            content, id_level, id_type
        )

        # kontrola kategorií
        id_level, id_type = cls._contains_settlement_categories(
            title, content, id_level, id_type
        )

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
        ib_prefix = r"{{\s*Infobox\s*"

        if re.search(ib_prefix + r"sídlo", content, re.I) or re.search(
            r"{\|.*?\|\s*sídlo.*?\|}", content, re.I | re.S
        ):
            return 1, "sídlo"
        if re.search(ib_prefix + r"\s*\w\s+obec", content, re.I):
            return 1, "obec"
        if re.search(ib_prefix + r"katastrálne\s+územie", content, re.I):
            return 1, "Slovenská obec"
        if re.search(ib_prefix + r"\s*\w\s+mesto", content, re.I):
            return 1, "mesto"

        if re.search(r"{{\s*Geobox\s*\|\s*Settlement", content, re.I):
            return 1, "mesto"

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

        if re.search(r"\[\[Kategória:Mestá\s+(?:na|v?)\s+.+?\]\]", content, re.I):
            id_level, id_type = 2, "Kategória Mestá..."
        elif re.search(r"\[\[Kategória:Obce\s+(?:na|v?)\s+.+?\]\]", content, re.I):
            id_level, id_type = 2, "Kategória Obce..."
        elif re.search(r"\[\[Kategória:Osady\s+(?:na|v?)\s+.+?\]\]", content, re.I):
            id_level, id_type = 2, "Kategória Osady..."
        elif re.search(r"\[\[Kategória:Prímorské\s*Letoviská\s+(?:na|v?)\s+.+?\]\]", content, re.I):
            id_level, id_type = 2, "Kategória Sídla..."

        if any(
            x in title.lower()
            for x in (
                "obec",
                "obc",
                "mest",
                "metro",
                "sídel",
                "sídl",
                "komún",
                "muze",
                "miesto",
                "dedin",
            )
        ):
            id_level, id_type = 0, ""

        return id_level, id_type

    def data_preprocess(self, content):
        """
        Předzpracování dat o sídlu.

        Parametry:
        content - obsah stránky (str)
        """
        content = content.replace("&nbsp;", " ")
        content = re.sub(r"m\sn\.\s*", "metrov nad ", content)

    def line_process_infobox(self, ln, is_infobox_block):
        # aliasy
        rexp_format = r"\|\s*názov\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))"
        rexp = re.search(rexp_format, ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox_sk.update(
                self.get_aliases(
                    self.del_redundant_text(rexp.group(1)), marked_slovak=True
                )
            )
            if is_infobox_block == True:
                return

        rexp_format = r"(?:názov|meno|nickname|official_name)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))"
        rexp = re.search(rexp_format, ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox.update(
                self.get_aliases(
                    self.del_redundant_text(
                        rexp.group(1), langmap=self.langmap)
                )
            )
            if is_infobox_block == True:
                return

        rexp_format = r"(?:iný\s+názov)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))"
        rexp = re.search(rexp_format, ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox_orig.update(
                self.get_aliases(
                    self.del_redundant_text(
                        rexp.group(1), langmap=self.langmap)
                )
            )
            if not len(self.aliases) and not len(self.aliases_infobox):
                self.first_alias = None

            if is_infobox_block == True:
                return

        # země
        if not self.country and re.search(
            r"{{\s*Infobox\s+(?:Slovenská\s+obec|štatutárne\s+mesto)", ln, re.I
        ):
            self.country = "Slovensko"
            if is_infobox_block == True:
                return

        if not self.country and re.search(r"{{\s*Infobox\s+Poľské\s+mesto", ln, re.I):
            self.country = "Poľsko"
            if is_infobox_block == True:
                return

        if not self.country:
            rexp = re.search(
                r"(?:krajina|štát|country)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
            if rexp and rexp.group(1):
                self.get_country(self.del_redundant_text(rexp.group(1)))
                if is_infobox_block == True:
                    return

        # počet obyvatel
        rexp = re.search(
            r"(?:obyvateľov|population)\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.get_population(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # rozloha
        rexp = re.search(
            r"(?:rozloha|výmera|area)\s*\w?\s*=(?!=)\s*((?:.+?)(?=\|[^\|]*\=)|(?:.*))", ln, re.I)
        if rexp and rexp.group(1):
            self.get_area(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

    def line_process_1st_sentence(self, ln):
        abbrs = "".join(
            (
                r"(?<!\s(?:tzv|atď))",
                r"(?<!\s(?:apod|(?:napr)))",
                r"(?<!\s(?:[amt]j|fr))",
                r"(?<!\d)",
                r"(?<!nad m)",
            )
        )
        rexp = re.search(
            r".*?'''.+?'''.*?\s(?:bol[aio]?|je|sú|nachádz(?:a|ajú)|patr(?:í|il)|stal|rozprestier|lež(?:í|al)).*?"
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
                    r"((?:{{(?:v\s*jazyku|lang|audio|cj|jazyk|vjz|cudzojazyčne|cjz)[^}]+}}\s+)?(?<!\]\]\s)'{3}.+?'{3})",
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
        country = re.sub(r"{{vlajka\s+a\s+názov\|(.*?)}}",
                         r"\1", country, flags=re.I)
        country = re.sub(r"{{.*?}}", "", country)
        country = (
            "Česká republika"
            if re.search(r"Čechy|Morava|Sliezsko", country, re.I)
            else country
        )
        country = re.sub(r",?\s*\(.*?\)", "", country)
        country = re.sub(r"\s+", " ", country).strip().replace("'", "")

        self.country = country

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
            r"{{(?:v\s*jazyku|lang|audio|cj|jazyk|vjz|cudzojazyčne|cjz)\|\w+\|(.*?)}}", r"\1", fs, flags=re.I
        )
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
        fs = re.sub(r"/.*?/", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r"^\s*}}", "", fs)  # Eliminate the end of a template
        fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",")
        fs = re.sub(r"\|(?:.+?)(?=\|[^\|]*\=)", "", fs)
        fs = re.sub(r"\|[^=]*=", "", fs)
        self.description = fs

    def get_population(self, population):
        """
        Převádí počet obyvatel sídla do jednotného formátu.

        Parametry:
        population - počet obyvatel sídla (str)
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
        population = "" if not re.search(r"\d", population) else population

        if coef and population:
            population = str(int(population) * coef)

        self.population = population

    def serialize(self):
        """
        Serializuje údaje o sídlu.
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
                self.country,
                self.latitude,
                self.longitude,
                self.area,
                self.population
            ]
        )
