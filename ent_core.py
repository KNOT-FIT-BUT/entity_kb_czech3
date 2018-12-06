#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autor: Michal Planička (xplani02)

Popis souboru:
Soubor obsahuje třídu 'EntCore', jež je rodičovskou třídou pro podtřídy entit.
"""

import re
from abc import ABCMeta, abstractmethod
from hashlib import md5, sha224
from libs.UniqueDict import *


class EntCore(metaclass=ABCMeta):
    """
    Abstraktní rodičovská třída, ze které dědí všechny entity.

    Instanční atributy:
    title - název entity (str)
    prefix - prefix entity (str)
    eid - ID entity (str)
    link - odkaz na Wikipedii (str)
    aliases - alternativní pojmenování entity (str)
    description - stručný popis entity (str)
    images - absolutní cesty k obrázkům Wikimedia Commons (str)

    Třídní atributy:
    counter - počítadlo instanciovaných objektů z odvozených tříd

    Metody:
    del_redundant_text(text) - odstraňuje přebytečné části textu, ale pouze ty, které jsou společné pro všechny získávané údaje
    get_image(image) - převádí název obrázku na absolutní cestu Wikimedia Commons
    """

    counter = 0
    LANG_CZECH = "cs"
    LANG_UNKNOWN = "???"

    @abstractmethod
    def __init__(self, title, prefix, link, redirects):
        """
        Inicializuje třídu 'EntCore'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        redirects - přesměrování Wiki stránek (dict)
        """

        # zvětšení počítadla instancí
        EntCore.counter += 1

        # inicializace základních údajů entity
        self.original_title = title
        self.title = re.sub(r"\s+\(.+?\)\s*$", "", title)
        self.prefix = prefix
        self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]  # vygenerování hashe
        self.link = link
        self.aliases = UniqueDict()
        self.description = ""
        self.images = ""
        self.n_marked_czech = 0
        self.first_alias = None
        self.redirects = redirects

    @staticmethod
    def del_redundant_text(text, multiple_separator = "|"):
        """
        Odstraňuje přebytečné části textu, ale pouze ty, které jsou společné pro všechny získávané údaje.

        Parametry:
        text - text, který má být upraven (str)
        multiple_separator - znak oddělující více řádků
#        clear_name_links - odstraňuje odkazy z názvů

        Návratová hodnota:
        Upravený text. (str)
        """

#        if clear_name_links:
#            clean_text = re.sub(r"(|\s*.*?název\s*=\s*(?!=)\s*.*?)\[\[[^\]]+\]\]", r"\1", text).strip() # odkaz v názvu zřejmě vede na jinou entitu (u jmen často odkazem napsán jazyk názvu)
#        else:
        clean_text = re.sub(r"\[\[[^\]|]+\|([^\]|]+)\]\]", r"\1", text)  # [[Sth (sth)|Sth]] -> Sth
        clean_text = re.sub(r"\[\[([^]]+)\]\]", r"\1", clean_text)  # [[Sth]] -> Sth
        clean_text = re.sub(r"'+(.+?)'+", r"\1", clean_text)  # '''Sth''' -> Sth
        clean_text = re.sub(r"\s*</?small>\s*", " ", clean_text)  # <small>sth</small> -> sth
#        clean_text = re.sub(r"\s*<br(?: ?/)?>\s*", ", ", clean_text)  # sth<br />sth -> sth, sth
        clean_text = re.sub(r"\s*<br(?: ?/)?>\s*", multiple_separator, clean_text)  # sth<br />sth -> sth, sth (sth-> sth | sth)
        clean_text = re.sub(r"\s*{{small\|([^}]+)}}\s*", r" \1", clean_text)  # {{small|sth}} -> sth
        clean_text = re.sub(r"\s*{{nowrap\|([^}]+)}}\s*", r" \1", clean_text, flags=re.I)  # {{nowrap|sth}} -> sth
        clean_text = re.sub(r"\s*{{(?:(?:doplňte|doplnit|chybí) zdroj|zdroj\?|fakt[^}]*)}}\s*", "", clean_text, flags=re.I)
        clean_text = clean_text.replace("{{--}}", "–")
        clean_text = clean_text.replace("{{break}}", ", ")
        clean_text = re.sub(r"\s*(?:{{•}}|•)\s*", ", ", clean_text)
        clean_text = clean_text.replace("&nbsp;", " ").replace("\xa0", " ")

        return clean_text


    def get_aliases(self, alias, marked_czech = False):
        """
        Převádí alternativní pojmenování do jednotného formátu.

        Parametry:
        alias - alternativní pojmenování entity (str)
        marked_czech - entita explicitně definovaná jako česká
        """
        # Eliminating of an alias identical with a title is now contraproductive, 'cause we need ensure that first alias is in czech language (it is eliminated in serializing step).
        if alias.strip() == "{{PAGENAME}}":
            return

        re_lang_aliases = re.compile("{{(?:Cj|Cizojazyčně|Vjazyce2)\|(?:\d=)?(\w+)\|(?:\d=)?([^}]+)}}", flags=re.I)
        lang_aliases = re_lang_aliases.findall(alias)

        alias = re.sub(r"\s+", " ", alias).strip()
        alias = re.sub(r"\s*<hr\s*/>\s*", "", alias)
        alias = alias.strip(",")
        alias = re.sub(r"(?:''|[„“\"])", "", alias)
        alias = re.sub(r"(?:,{2,}|;)\s*", ", ", alias)
        alias = re.sub(r"\s+/\s+", ", ", alias)
        alias = re.sub(r"\s*<hiero>.*</hiero>\s*", "", alias, flags=re.I)
        alias = re.sub(r"\s*{{Poznámka pod čarou.*(?:}})?\s*$", "", alias, flags=re.I)
        alias = re.sub(r"\s*\{{Unicode\|([^}]+)}}\s*", r" \1", alias, flags=re.I)
        alias = re.sub(r"\s*\({{(?:Cj|Cizojazyčně)\|(?:\d=)?\w+\|(?:\d=)?[^}]+}}\)\s*", "", alias, flags=re.I) # aliases are covered by "lang_aliases"
        alias = re.sub(r"\s*{{(?:Cj|Cizojazyčně)\|(?:\d=)?\w+\|(?:\d=)?[^}]+}}\s*", "", alias, flags=re.I) # aliases are covered by "lang_aliases"
        alias = re.sub(r"\s*\({{V ?jazyce2\|\w+\|[^}]+}}\)\s*", "", alias, flags=re.I) # aliases are covered by "lang_aliases"
        alias = re.sub(r"\s*\(?{{V ?jazyce\|\w+}}\)?:?\s*", "", alias, flags=re.I)
        alias = re.sub(r"\s*\(?{{(?:Jaz|Jazyk)\|[\w-]+\|([^}]+)}}\)?:?\s*", r"\1", alias, flags=re.I)
        alias = re.sub(r"\s*{{(?:Malé|Velké)\|(.*?)}}\s*", r"\1", alias, flags=re.I)
        if re.search(r"\s*{{Možná hledáte", alias, flags=re.I):
            alias = re.sub(r"\s*{{Možná hledáte|([^=|])*?}}\s*", r"\1", alias, flags=re.I)
            alias = re.sub(r"\s*{{Možná hledáte|.*?jiné\s*=\s*([^|])*?.*?}}\s*", r"\1", alias, flags=re.I)
        # TODO: přidat šablonu přesměrování
        alias = re.sub(r"\s*{{[a-z]{2}}};?\s*", "", alias)
        alias = re.sub(r"\s*\[[^]]+\]\s*", "", alias)
        alias = re.sub(r",(?!\s)", ", ", alias)
        alias = alias.replace(",|", "|")
        alias = re.sub(r"[\w\s\-–—−,.()]+:\s*\|?", "", alias)
        alias = re.sub(r"\s*\([^)]+\)\s*", " ", alias)
        alias = alias.strip(",")
        alias = re.sub(r"\|{2,}", "|", alias)
        alias = re.sub(r"^(\s*\|\s*)+$", "", alias)
        alias = self.custom_transform_alias(alias)
        alias = re.sub(r"^viz(\.|\s)", "", alias) # vyhození navigačního slova "viz" - například "viz něco" -> "něco"
        alias = re.sub(r"{{[^}]+?}}", "", alias) # vyhození ostatních šablon (nové šablony by dělaly nepořádek)
        alias = re.sub(r"[()\[\]{}]", "", alias)
        alias = re.sub(r"<.*?>", "", alias)
        for a in alias.split("|"):
            a = a.strip()
            if re.search(r"[^\W_]", a):
                if marked_czech:
                    self.aliases[a] = self.LANG_CZECH
                    self.n_marked_czech += 1

                else:
                    if self.first_alias == None:
                        self.first_alias = a
                    self.aliases[a] = None

        for lng, a in lang_aliases:
            a = a.strip()
            # TODO: maybe, it is needed custom_transform_alias()?
            if re.search(r"[^\W_]", a):
                if not len(self.aliases):
                    self.first_alias = a
                self.aliases[a] = lng


    def custom_transform_alias(self, alias):
        """
        Umožňuje provádět vlastní transformace aliasů entity do jednotného formátu.

        Parametry:
        alias - alternativní pojmenování entity (str)
        """
        return alias


    def transform_geo_alias(self, alias):
        """
        Přidává další transformační pravidla specifická pro aliasy různých geografických entit.

        Parametry:
        alias - alternativní pojmenování geografické entity (str)
        """

        alias = re.sub(r"\s*{{flagicon.*?}}\s*", "", alias, flags=re.I)
        alias = re.sub(r"\s*(,,|/,)\s*", ", ", alias)
        alias = re.sub(r"\s*[,/;]\s*", "|", alias)
        alias = re.sub(r"malé\|", "", alias, flags=re.I)
#        alias = alias.replace(", ", "|") # Původně bylo jen pro country.. Nedostávají se tam i okresy, kraje apod? (U jmen nelze kvůli titulům za jménem)

        return alias


    def serialize_aliases(self):
        """
        Serialized aliases to be written while creating KB
        """
        if (self.n_marked_czech == 0 and self.first_alias and len(self.aliases.keys()) > 0):
#            if self.first_alias in self.aliases:
#               self.aliases.pop(self.first_alias, None)
            self.aliases[self.first_alias] = self.LANG_CZECH

        self.aliases.pop(self.title, None)
#        possible_czech = all(lang in [self.LANG_CZECH, None] for alias, lang in self.aliases.items())

        preserialized = set()
        for alias, lang in self.aliases.items():
#            preserialized.add(alias + "#lang=" + (self.LANG_CZECH if (possible_czech and lang in [None, self.LANG_CZECH]) else (lang if lang != None else self.LANG_UNKNOWN)))
            preserialized.add(alias + "#lang=" + (lang if lang != None else self.LANG_UNKNOWN))

        return "|".join(preserialized)


    def get_image(self, image):
        """
        Převádí název obrázku na absolutní cestu Wikimedia Commons.

        Parametry:
        image - název obrázku (str)
        """

        image = re.sub(r"{{.*$", "", image) # remove templates with descriptions from image path
        image = re.sub(r"\s*\|.*$", "", image).replace("}", "").strip().replace(" ", "_")
        image_hash = md5(image.encode("utf-8")).hexdigest()[:2]
        image = "wikimedia/commons/" + image_hash[0] + "/" + image_hash + "/" + image

        self.images += image if not self.images else "|" + image

        # starý způsob extrakce - prozatím nemazat
        # try:
        #     url_res = urlopen("https://cs.wikipedia.org/wiki/" + quote("Soubor:" + image))
        # except (HTTPError, URLError) as err:
        #     print("[[ Chyba obrázku ]] " + str(err.reason) + " :: " + str(image))
        # except OSError as err:
        #     print("[[ Chyba obrázku ]] " + str(err.strerror) + " :: " + str(image))
        # else:
        #     try:
        #         url_data = str(url_res.read())
        #     except IncompleteRead as e:
        #         url_data = str(e.partial)
        #     url_res.close()
        #     path_re = re.search("wikipedia/commons/[^/]{1,2}/[^/]{1,2}/", url_data)
        #     if path_re:
        #         full_path = path_re.group(0).replace("wikipedia", "wikimedia") + image
        #         self.images += full_path if not self.images else "|" + full_path
