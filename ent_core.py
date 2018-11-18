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

    @abstractmethod
    def __init__(self, title, prefix, link):
        """
        Inicializuje třídu 'EntCore'.

        Parametry:
        title - název stránky (str)
        prefix - prefix entity (str)
        link - odkaz na Wikipedii (str)
        """

        # zvětšení počítadla instancí
        EntCore.counter += 1

        # inicializace základních údajů entity
        self.title = title
        self.prefix = prefix
        self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]  # vygenerování hashe
        self.link = link
        self.aliases = ""
        self.description = ""
        self.images = ""

    @staticmethod
    def del_redundant_text(text):
        """
        Odstraňuje přebytečné části textu, ale pouze ty, které jsou společné pro všechny získávané údaje.

        Parametry:
        text - text, který má být upraven (str)

        Návratová hodnota:
        Upravený text. (str)
        """

        clean_text = re.sub(r"\[\[[^\]|]+\|([^\]|]+)\]\]", r"\1", text)  # [[Sth (sth)|Sth]] -> Sth
        clean_text = re.sub(r"\[\[([^]]+)\]\]", r"\1", clean_text)  # [[Sth]] -> Sth
        clean_text = re.sub(r"'+(.+?)'+", r"\1", clean_text)  # '''Sth''' -> Sth
        clean_text = re.sub(r"\s*</?small>\s*", " ", clean_text)  # <small>sth</small> -> sth
        clean_text = re.sub(r"\s*<br(?: ?/)?>\s*", ", ", clean_text)  # sth<br />sth -> sth, sth
        clean_text = re.sub(r"\s*{{small\|([^}]+)}}\s*", r" \1", clean_text)  # {{small|sth}} -> sth
        clean_text = re.sub(r"\s*{{nowrap\|([^}]+)}}\s*", r" \1", clean_text, flags=re.I)  # {{nowrap|sth}} -> sth
        clean_text = re.sub(r"\s*{{(?:(?:doplňte|doplnit|chybí) zdroj|zdroj\?|fakt[^}]*)}}\s*", "", clean_text, flags=re.I)
        clean_text = clean_text.replace("{{--}}", "–")
        clean_text = clean_text.replace("{{break}}", ", ")
        clean_text = re.sub(r"\s*(?:{{•}}|•)\s*", ", ", clean_text)
        clean_text = clean_text.replace("&nbsp;", " ").replace("\xa0", " ")

        return clean_text

    def get_image(self, image):
        """
        Převádí název obrázku na absolutní cestu Wikimedia Commons.

        Parametry:
        image - název obrázku (str)
        """

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
