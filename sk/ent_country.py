#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_slovak3 (https://knot.fit.vutbr.cz/wiki/index.php/entity_kb_slovak3)
Autori:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)
    Samuel Križan (xkriza06)

Popis souboru:
Soubor obsahuje třídu 'EntCountry', která uchovává údaje o státech.
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

    def __init__(self, title, prefix, link, redirects, langmap):
        """
        Inicializuje třídu 'EntCountry'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """

        super(EntCountry, self).__init__(
            title, prefix, link, redirects, langmap)

        self.area = ""
        self.population = ""

        self.re_infobox_kw_img = r"(?:vlajka|znak|mapa[\s_]poloha)"

        self.get_wiki_api_data()

    @staticmethod
    def is_country(content):
        """
        Na základě obsahu stránky určuje, zda stránka pojednává o státu, či nikoliv.

        Parametry:
        content - obsah stránky (str)

        Návratové hodnoty:
        1 v případě, že stránka pojednává o státu, jinak 0. (int)
        """

        try:

            # kontrola kategorií - začátek
            # státy podle kontinentů
            rexp_format = "Štáty\s+v\s+(?:Afrike|Ázii|Austrálii\s+a\s+Oceánii|Európe|(?:Severnej|Južnej)\s+Amerike)"
            if re.search(r"\[\[\s*Kategória:\s*" + rexp_format + r"\s*\]\]", content, re.I):
                return 1
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)

        # státy podle mezinárodních organizací
        if re.search(
            r"\[\[\s*Kategória:\s*Členovia\s+(?:NATO|EÚ|OSN|Commonwealthu)\s*\]\]",
            content,
            re.I,
        ):
            return 1

        # neuznané či jen částečně uznané státy
        if re.search(
            r"\[\[\s*Kategória:\s*Neuznané\s+štáty\s*\]\]",
            content,
            re.I,
        ):
            return 1

        if re.search(
           r"\[\[\s*Kategória:\s*Zaniknuté\s+štáty\s*\w",
            content,
            re.I,
           ):
            return 1
        # kontrola kategorií - konec

        return 0

    def data_preprocess(self, content):
        """
        Předzpracování dat o státu.

        Parametry:
        content - obsah stránky (str)
        """

        # prefix - zaniklé státy
        if re.search(
            r"\[\[\s*Kategória:\s*Zaniknuté\s+štáty\s*\w",
            content,
            re.I,
        ):
            self.prefix = "country:former"

    def line_process_infobox(self, ln, is_infobox_block):
        rexp = re.search(r"\| Celý názov\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.aliases_infobox_sk.update(
                self.get_aliases(
                    self.del_redundant_text(rexp.group(1)), marked_slovak=True
                )
            )
            if len(self.aliases_infobox):
                self.aliases_infobox_orig.update(self.aliases_infobox)
                self.aliases_infobox.clear()
                if not len(self.aliases):
                    self.first_alias = None
            if is_infobox_block == True:
                return

        # aliases - common name may contain name in local language
        rexp = re.search(r"\| Dlhý miestny názov\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            aliases = self.get_aliases(self.del_redundant_text(rexp.group(1)))
            if len(self.aliases_infobox_sk):
                var_aliases = self.aliases_infobox_orig
                if not len(self.aliases):
                    self.first_alias = None
            else:
                var_aliases = self.aliases_infobox
            var_aliases.update(aliases)

            if is_infobox_block == True:
                return

        # počet obyvatel
        rexp = re.search(
            r"\| Sčítanie počtu obyvateľov\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_population(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        # rozloha
        rexp = re.search(r"\| Rozloha\s*=(?!=)\s*(.*)", ln, re.I)
        if rexp and rexp.group(1):
            self.get_area(self.del_redundant_text(rexp.group(1)))
            if is_infobox_block == True:
                return

        rexp = re.search(r"Medzinárodný kód\s*=(?!=)\s*(\w*)", ln, re.I)
        if rexp and rexp.group(1):
            self.lang_orig = rexp.group(1).lower()
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
            )
        )
        rexp = re.search(
            r".*?'''.+?'''.*?\s(?:bol[aiy]?|je|sú|nachádz(?:a|ajú)|patr(?:í|il)|stal|rozprostier(?:a|al)|lež(?:í|al)).*?"
            + abbrs
            + "\.(?![^[]*?\]\])",
            ln,
        )
        if self.title == "Druhá česko-slovenská republika":
            rexp = re.search(
                r".*?'''.+?'''.*?\s(?:bol[aiy]?|je|sú|nachádz(?:a|ajú)|patr(?:í|il)|stal|rozprostier(?:a|al)|lež(?:í|al)).*?"
                + "\.(?![^[]*?\]\])",
                ln,
            )

        if rexp:
            if not self.description:
                self.get_first_sentence(
                    self.del_redundant_text(rexp.group(0), ", "))

                tmp_first_sentence = rexp.group(0)
                # TODO: refactorize + give this to other entity types
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
                    r"((?:{{(?:v\s*jazyku|lang|cj|jazyk|vjz|cudzojazyčne|cjz)[^}]+}}\s+)?(?<!\]\]\s)'{3}.+?'{3})",
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
                fs_aliases = re.findall(
                    re.escape(self.title) + r"\s+\((.+?)\)", rexp.group(0)
                )
                if fs_aliases:
                    for fs_alias in fs_aliases:
                        self.aliases.update(
                            self.get_aliases(self.del_redundant_text(fs_alias))
                        )
                fs_aliases = re.search(
                    r"(?:\s+niekedy)?\s+(?:označovan[áéýí]||nazývan[áéýí])(?:\s+(?:(?:(?:i|aj|tiež)\s+)?ako)|i|aj|tiež)?\s+(''.+?''|{{.+?}})(.+)",
                    rexp.group(0),
                )
                if fs_aliases:
                    self.aliases.update(
                        self.get_aliases(
                            self.del_redundant_text(
                                fs_aliases.group(1)).strip("'")
                        )
                    )
                    fs_next_aliases = re.finditer(
                        r"(?:,|\s+alebo)(?:\s+(?:(?:(?:i|aj|tiež)\s+)?ako)|i|aj|tiež)?\s+(''.+?''|{{.+?}})",
                        fs_aliases.group(2),
                    )
                    for fs_next_alias in fs_next_aliases:
                        self.aliases.update(
                            self.get_aliases(
                                self.del_redundant_text(
                                    fs_next_alias.group(1).strip("'")
                                )
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
        # TODO: refactorize
        fs = re.sub(
            r"{{(?:v\s*jazyku|lang|audio|cj|jazyk|vjz|cudzojazyčne|cjz)\|.*?\|(.+?)}}",
            r"\1",
            fs,
            flags=re.I,
        )
        fs = re.sub(r"{{IPA\d?\|(.+?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{výslovnosť\|(.+?)\|.*?}}", r"", fs, flags=re.I)
        fs = re.sub(
            r"{{čínsky(.+?)}}",
            lambda x: re.sub(
                "(?:znaky|pchin-jin|tradičné|zjednodušené|pinyin)"
                "\s*=\s*(.*?)(?:\||}})",
                r"\1 ",
                x.group(1),
                flags=re.I,
            ),
            fs,
            flags=re.I,
        )
        fs = re.sub(r"{{malé\|(.*?)}}", r"\1", fs, flags=re.I)
        fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
        fs = re.sub(r"{{.*?}}", "", fs)
        fs = re.sub(r"<.*?>", "", fs)
        fs = re.sub(r"\(.*?\)", "", fs)
        fs = re.sub(r"\s+", " ", fs).strip()
        fs = re.sub(r" ([,.])", r"\1", fs)
        fs = re.sub(r"^\s*}}", "", fs)  # Eliminate the end of a template
        fs = fs.replace("''", "").replace(")", "").replace(
            "|group=pozn.}}", "")
        fs = re.sub(r"\|(?:.+?)(?=\|[^\|]*\=)", "", fs)
        fs = re.sub(r"\|[^=]*=", "", fs)
        self.description = fs

    def get_population(self, population):
        """
        Převádí počet obyvatel státu do jednotného formátu.

        Parametry:
        population - počet obyvatel státu (str)
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
        Serializuje údaje o státu.
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
                self.latitude,
                self.longitude,
                self.area,
                self.population
            ]
        )
