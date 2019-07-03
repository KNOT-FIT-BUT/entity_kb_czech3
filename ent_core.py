#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autoři:
    Michal Planička (xplani02)
    Tomáš Volf (ivolf)

Popis souboru:
Soubor obsahuje třídu 'EntCore', jež je rodičovskou třídou pro podtřídy entit.
"""

import re
import sys
from abc import ABCMeta, abstractmethod
from hashlib import md5, sha224
from libs.DictOfUniqueDict import *


TAG_BRACES_OPENING = '{{'
TAG_BRACES_CLOSING = '}}'


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
    KEY_LANG = 'lang'
    KEY_NAMETYPE = 'ntype'
    LANG_CZECH = "cs"
    LANG_UNKNOWN = "???"
    NTYPE_QUOTED = "quoted"

    @abstractmethod
    def __init__(self, title, prefix, link, redirects, langmap):
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
        self.aliases = DictOfUniqueDict()
        self.description = ""
        self.images = ""
        self.n_marked_czech = 0
        self.first_alias = None
        self.redirects = redirects
        self.langmap = langmap
        self.re_infobox_kw_img = r"obrázek"

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
        clean_text = re.sub(r"'{2,}(.+?)'{2,}", r"\1", clean_text)  # '''Sth''' -> Sth
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


    def get_data(self, content):
        """
        Extract data of entity from the content of page.

        Parameters:
        * content - content of the page (str)
        """

        self.data_preprocess(content)

        try:
            data = content.splitlines()
        except AttributeError:
            pass
        else:
            is_infobox = False
            is_infobox_block = None   # True = Block infobox / False = Inline (or combined) infobox / None = Unknown
            was_infobox = False       # We accept only the 1st one infobox
            maybe_infobox_end = False # Determines, whether an end of infobox could be found
            is_infobox_unesco = False # Determines infobox "světové dědictví"
            for ln in data:
                part_text = None
                part_infobox = ln

                # Image located in infobox - but not only the first one, so implementation is located here
                rexp = re.search(self.re_infobox_kw_img + r"\s*=(?!=)\s*(.*)", ln, re.I)
                if rexp and rexp.group(1):
                    self.get_image(self.del_redundant_text(rexp.group(1)))

                # Common image
                ln = self.process_and_clean_common_images(ln)


                if not is_infobox:
                    # If it is not infobox already, explore if it is an infobox
                    infobox_data = re.search(r"{{Infobox([^\|]+)(\|)?.*$", ln, flags = re.I)
                    if infobox_data:
                        if re.search(r"světové\s+dědictví", infobox_data.group(1), flags = re.I):
                            is_infobox_unesco = True
                        ln = infobox_data.group(0)
                        # Empty infobox
                        ln_infobox_start = re.search(r"Infobox[^{]*}}\s*([^\s].*(?!}}))?$", ln, flags = re.I)
                        if ln_infobox_start:
                            # Line containing empty infobox as well as first paragraph
                            # for example: {{Infobox - osoba}}'''Masao Mijamoto''' ...
                            if ln_infobox_start.group(1):
                                part_text = ln_infobox_start.group(1)
                            # Line containing empty infobox only, for example: {{Infobox - osoba}}
                            else:
                                continue
                        else:
                            infobox_braces_depth = 0
                            is_infobox = True
                            # If pipe char is present, it is inline or combined infobox, otherwise it is block infobox
                            if infobox_data.group(2):
                                is_infobox_block = False
                            else:
                                is_infobox_block = True
                    else:
                        part_text = ln

                # If line contains infobox, explore if contains the end tag of infobox
                if is_infobox:
                    l_braces = self.getOpeningBracesPosition(ln)
                    r_braces = self.getClosingBracesPosition(ln)
                    while True:
                        if l_braces >= 0:
                            if r_braces >= 0:
                                if l_braces < r_braces:
                                    infobox_braces_depth += 1
                                    l_braces = self.getOpeningBracesPosition(ln, l_braces)
                                else:
                                    infobox_braces_depth -= 1
                                    if infobox_braces_depth > 0:
                                        r_braces = self.getClosingBracesPosition(ln, r_braces)
                            else:
                                l_braces = self.getOpeningBracesPosition(ln, l_braces)
                                infobox_braces_depth += 1
                        else:
                            if r_braces >= 0:
                                infobox_braces_depth -= 1
                                if infobox_braces_depth > 0:
                                    r_braces = self.getClosingBracesPosition(ln, r_braces)
                            else:
                                break
                        if infobox_braces_depth == 0:
                            is_infobox = False
                            part_infobox = ln[:r_braces]
                            part_text = ln[(r_braces + len(TAG_BRACES_CLOSING)):].strip()
                            break

                    if not was_infobox:
                        # If line belongs to infobox and infobox was already not present and is not UNESCO infobox, process it
                        if not is_infobox_unesco:
                            self.line_process_infobox(part_infobox, is_infobox_block)
                            if infobox_braces_depth == 0:
                                was_infobox = True
                        is_infobox_block = None


                if part_text:
                    self.line_process_1st_sentence(part_text)

            return self.serialize()


    def getTagPosition(self, tag, ln, lastPosition = None):
        if lastPosition != None:
            findFrom = lastPosition + len(tag)
        else:
            findFrom = 0
        return ln.find(tag, findFrom)


    def getOpeningBracesPosition(self, ln, lastPosition = None):
        return self.getTagPosition(TAG_BRACES_OPENING, ln, lastPosition)

    def getClosingBracesPosition(self, ln, lastPosition = None):
        return self.getTagPosition(TAG_BRACES_CLOSING, ln, lastPosition)


    def data_preprocess(self, content):
        """
        Entity data preprocessing - method designed for override in child method (not designed as abstract!!)

        Parameters:
        * content - content of page (str)
        """
        return


    def line_process_infobox(self, line, is_infobox_bloxk):
        """
        Processing of infobox line - method designed for override in child method (not designed as abstract!!)

        Parameters:
        * line - line of the content of page (str)
        * is_infobox_block - type of infobox (True = block; False = inline (or combined); None = unknown)
        """
        return


    def line_process_1st_sentence(self, line):
        """
        Processing of first sentence - method designed for override in child method (not designed as abstract!!)

        Parameters:
        * line - line of the content of page (str)
        """
        return

    def serialize(self):
        """
        Entity data serializing - method designed for override in child method (not designed as abstract!!)
        """
        return


    def get_aliases(self, alias, marked_czech = False, nametype = None):
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
        re_lang_aliases2 = re.compile("{{Vjazyce\|(\w+)}}\s+([^{]{2}.+)", flags=re.I)
        lang_aliases = re_lang_aliases.findall(alias)
        lang_aliases += re_lang_aliases2.findall(alias)
        alias = re.sub(r"\s+", " ", alias).strip()
        alias = re.sub(r"\s*<hr\s*/>\s*", "", alias)
        alias = alias.strip(",")
        alias = re.sub(r"(?:'')", "", alias)
        alias = re.sub(r"(?:,{2,}|;)\s*", ", ", alias)
        alias = re.sub(r"\s+/\s+", ", ", alias)
        alias = re.sub(r"\s*<hiero>.*</hiero>\s*", "", alias, flags=re.I)
        alias = re.sub(r"\s*{{Poznámka pod čarou.*(?:}})?\s*$", "", alias, flags=re.I)
        alias = re.sub(r"\s*\{{Unicode\|([^}]+)}}\s*", r" \1", alias, flags=re.I)
        alias = re.sub(r"\s*\({{(?:Cj|Cizojazyčně)\|(?:\d=)?\w+\|(?:\d=)?[^}]+}}\)\s*", "", alias, flags=re.I) # aliases are covered by "lang_aliases"
        alias = re.sub(r"\s*{{(?:Cj|Cizojazyčně)\|(?:\d=)?\w+\|(?:\d=)?[^}]+}}\s*", "", alias, flags=re.I) # aliases are covered by "lang_aliases"
        alias = re.sub(r"\s*\({{V ?jazyce2\|\w+\|[^}]+}}\)\s*", "", alias, flags=re.I) # aliases are covered by "lang_aliases"
        alias = re.sub(r"\s*\(?{{V ?jazyce\|\w+}}\)?:?\s*", "", alias, flags=re.I) # aliases are covered by "lang_aliases"
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
        alias = re.sub(r"[„“”]", "\"", alias) # quotation unification

        for a in alias.split("|"):
            a = a.strip()
            if re.search(r"[^\W_]", a):
                if marked_czech:
                    self.scrape_quoted_inside_and_store(a, nametype, self.LANG_CZECH)
                    self.n_marked_czech += 1

                else:
                    if self.first_alias == None and nametype == None:
                        self.first_alias = a
                    self.scrape_quoted_inside_and_store(a, nametype)

        for lng, a in lang_aliases:
            a = a.strip()
            # TODO: maybe, it is needed custom_transform_alias()?
            if re.search(r"[^\W_]", a):
                if not len(self.aliases):
                    self.first_alias = a
                self.scrape_quoted_inside_and_store(a, nametype, lng)


    def scrape_quoted_inside_and_store(self, alias, nametype, lang = None):
        if not alias.startswith('"') or not alias.endswith('"'):
            self.store_alias(alias, nametype, lang)

        quotedNames = []
        while True:
            quotedName = re.search(r"(?P<quote>[\"])(.+?)(?P=quote)", alias)

            if quotedName:
                quotedNames.append(quotedName.group(2))
                alias = re.sub(re.escape(quotedName.group(0)), "", alias)
            else:
                break

        if len(quotedNames):
            for qn in quotedNames:
                self.store_alias(qn, self.NTYPE_QUOTED, lang)

            self.store_alias(alias, nametype, lang)


    def store_alias(self, a, nametype, lang = None):
        self.aliases[a][self.KEY_LANG] = lang
        self.aliases[a][self.KEY_NAMETYPE] = nametype


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
        alias = re.sub(r"\s*(?:[,;]|(?<!<)/)\s*", "|", alias)
        alias = re.sub(r"malé\|", "", alias, flags=re.I)
#        alias = alias.replace(", ", "|") # Původně bylo jen pro country.. Nedostávají se tam i okresy, kraje apod? (U jmen nelze kvůli titulům za jménem)

        return alias


    def serialize_aliases(self):
        """
        Serialized aliases to be written while creating KB
        """
        if (self.n_marked_czech == 0 and self.first_alias and len(self.aliases.keys()) > 0):
            self.aliases[self.first_alias][self.KEY_LANG] = self.LANG_CZECH

        self.aliases.pop(self.title, None)

        preserialized = set()
        for alias, properties in self.aliases.items():
            tmp_flags = ""
            for key, value in properties.items():
#                preserialized.add(alias + "#lang=" + (self.LANG_CZECH if (possible_czech and lang in [None, self.LANG_CZECH]) else (lang if lang != None else self.LANG_UNKNOWN)))
                if key == self.KEY_LANG and value == None:
                    value = self.LANG_UNKNOWN
                if key != self.KEY_NAMETYPE or value != None:
                    tmp_flags += '#' + key + '=' + value
            preserialized.add(alias + tmp_flags)

        return "|".join(preserialized)


    def process_and_clean_common_images(self, line):
        """
        Process common image, transform it to Wikimedia Commons absolute path and return the rest of line without this common image

        Parameters:
        * line - input line of wiki page (str)
        """

        retval = False
        images = re.findall(r"(\[\[(?:Soubor|File):([^|]+?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg))(?:\|(?:[^\[\]]|\[\[[^\]]+\]\]|(?<!\[)\[[^\[\]]+\])*)*\]\])", line, re.I)
        for image in images:
            if image[1]:
                self.get_image(image[1])
                line = line.replace(image[0], "")

        return line


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
