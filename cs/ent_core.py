
import re, regex
import requests
import sys
from abc import ABCMeta, abstractmethod
from hashlib import md5, sha224
from libs.DictOfUniqueDict import *
from libs.UniqueDict import KEY_LANG, LANG_ORIG, LANG_UNKNOWN


TAG_BRACES_OPENING = "{{"
TAG_BRACES_CLOSING = "}}"

ALIASES_SEPARATOR = re.escape(", ")

WIKI_API_URL = "https://cs.wikipedia.org/w/api.php"
WIKI_API_PARAMS_BASE = {
	"action": "query",
	"format": "json",
}


class EntCore(metaclass=ABCMeta):

	counter = 0
	KEY_NAMETYPE = "ntype"
	LANG_CZECH = "cs"
	NTYPE_QUOTED = "quoted"

	@abstractmethod
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):

		# zvětšení počítadla instancí
		EntCore.counter += 1

		# vygenerování hashe
		self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]
		self.prefix = prefix
		self.original_title = title
		self.title = re.sub(r"\s+\(.+?\)\s*$", "", title)
		self.link = link
		self.images = ""
		self.description = ""
		self.langmap = langmap
		self.redirects = redirects
		
		# self.aliases = []
		self.aliases = DictOfUniqueDict()
		self.aliases_infobox = DictOfUniqueDict()
		self.aliases_infobox_cz = DictOfUniqueDict()
		self.aliases_infobox_orig = DictOfUniqueDict()
		self.n_marked_czech = 0
		self.first_alias = None
		self.infobox_type = None
		self.latitude = ""
		self.longitude = ""

		self.infobox_data = data["data"]
		self.infobox_name = data["name"]
		self.categories = data["categories"]
		self.first_paragraph = data["paragraph"]
		self.coords = data["coords"]

		self.extract_images()

	##
	# @brief serializes entity data for output (tsv format)
	# @param ent_data - child entity data that is merged with general data <tsv string>
	# @return tab separated values containing all of entity data <string>
	def serialize(self, ent_data):
		data = "\t".join([
			self.eid,
			self.prefix,
			self.title,
			# "|".join(self.aliases),
			self.serialize_aliases() if self.prefix != "person:group" else "",
			"|".join(self.redirects),
			self.description,
			self.original_title,
			self.images,
			self.link,
			ent_data
		]).replace("\n", "")
		return data

	def get_wiki_api_location(self, title):
		wiki_api_params = WIKI_API_PARAMS_BASE.copy()
		wiki_api_params["prop"] = "coordinates"
		wiki_api_params["titles"] = title
		try:
			r = requests.get(WIKI_API_URL, params=wiki_api_params)
			pages = r.json()["query"]["pages"]
			first_page = next(iter(pages))
			if first_page != "-1":
				self.latitude = pages[first_page]["coordinates"][0]["lat"]
				self.longitude = pages[first_page]["coordinates"][0]["lon"]
		except Exception as e:
			self.latitude = ""
			self.longitude = ""

	def get_latitude(self, latitude):
		"""
		Převádí zeměpisnou šířku geografické entity do jednotného formátu.

		Parametry:
		latitude - zeměpisná šířka geografické entity (str)
		"""
		latitude = re.sub(r"\(.*?\)", "", latitude)
		latitude = re.sub(r"\[.*?\]", "", latitude)
		latitude = re.sub(r"<.*?>", "", latitude)
		latitude = re.sub(r"{{.*?}}", "", latitude).replace("{", "").replace("}", "")
		latitude = re.sub(r"(?<=\d)\s(?=\d)", "", latitude).strip()
		latitude = re.sub(r"(?<=\d)\.(?=\d)", ",", latitude)
		latitude = re.sub(r"^[^\d-]*(?=\d)", "", latitude)
		latitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", latitude)
		latitude = "" if not re.search(r"\d", latitude) else latitude

		self.latitude = latitude

	def get_longitude(self, longitude):
		"""
		Převádí zeměpisnou délku geografické entity do jednotného formátu.

		Parametry:
		longitude - zeměpisná délka geografické entity (str)
		"""
		longitude = re.sub(r"\(.*?\)", "", longitude)
		longitude = re.sub(r"\[.*?\]", "", longitude)
		longitude = re.sub(r"<.*?>", "", longitude)
		longitude = re.sub(r"{{.*?}}", "", longitude).replace("{", "").replace("}", "")
		longitude = re.sub(r"(?<=\d)\s(?=\d)", "", longitude).strip()
		longitude = re.sub(r"(?<=\d)\.(?=\d)", ",", longitude)
		longitude = re.sub(r"^[^\d-]*(?=\d)", "", longitude)
		longitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", longitude)
		longitude = "" if not re.search(r"\d", longitude) else longitude

		self.longitude = longitude

	@staticmethod
	def del_redundant_text(text, multiple_separator="|", langmap=dict()):
		"""
				Odstraňuje přebytečné části textu, ale pouze ty, které jsou společné pro všechny získávané údaje.

				Parametry:
				text - text, který má být upraven (str)
				multiple_separator - znak oddělující více řádků
				clear_name_links - odstraňuje odkazy z názvů

				Návratová hodnota:
				Upravený text. (str)
		"""

		#        if clear_name_links:
		#            clean_text = re.sub(r"(|\s*.*?název\s*=\s*(?!=)\s*.*?)\[\[[^\]]+\]\]", r"\1", text).strip() # odkaz v názvu zřejmě vede na jinou entitu (u jmen často odkazem napsán jazyk názvu)
		#        else:
		link_lang = re.search(r"\[\[(.*?)(?:\|.*?)?\]\]\s*(<br(?: ?/)?>)?", text)
		if link_lang and link_lang.group(1):
			txt_lang = link_lang.group(1).lower()
			if txt_lang in langmap:
				text = text.replace(
					link_lang.group(0), "{{{{Vjazyce|{}}}}} ".format(langmap[txt_lang])
				)
		clean_text = re.sub(
			r"\[\[[^\]|]+\|([^\]|]+)\]\]", r"\1", text
		)  # [[Sth (sth)|Sth]] -> Sth
		clean_text = re.sub(r"\[\[([^]]+)\]\]", r"\1", clean_text)  # [[Sth]] -> Sth
		clean_text = re.sub(r"'{2,}(.+?)'{2,}", r"\1", clean_text)  # '''Sth''' -> Sth
		clean_text = re.sub(
			r"\s*</?small>\s*", " ", clean_text
		)  # <small>sth</small> -> sth
		#        clean_text = re.sub(r"\s*<br(?: ?/)?>\s*", ", ", clean_text)  # sth<br />sth -> sth, sth
		clean_text = re.sub(
			r"\s*<br(?: ?/)?>\s*", multiple_separator, clean_text
		)  # sth<br />sth -> sth, sth (sth-> sth | sth)
		clean_text = re.sub(
			r"\s*{{small\|([^}]+)}}\s*", r" \1", clean_text
		)  # {{small|sth}} -> sth
		clean_text = re.sub(
			r"\s*{{nowrap\|([^}]+)}}\s*", r" \1", clean_text, flags=re.I
		)  # {{nowrap|sth}} -> sth
		clean_text = re.sub(
			r"\s*{{(?:(?:doplňte|doplnit|chybí) zdroj|zdroj\?|fakt[^}]*)}}\s*",
			"",
			clean_text,
			flags=re.I,
		)
		clean_text = clean_text.replace("{{--}}", "–")
		clean_text = clean_text.replace("{{break}}", ", ")
		clean_text = re.sub(r"\s*(?:{{•}}|•)\s*", ", ", clean_text)
		clean_text = clean_text.replace("&nbsp;", " ").replace("\xa0", " ")

		return clean_text

	def unfold_alias_variants(self, alias):
		# workaround for Ludvík z Pruska:
		alias_variants = [alias]
		alias_matches = re.match(r"(.*[^\s])\s*/\s*([^\s].*)", alias)
		if alias_matches:
			alias_variant_1st = alias_matches.group(1)
			alias_variant_2nd = alias_matches.group(2)

			alias_variants.append(
				alias_variant_1st
			)  # Alias1 / Alias2 -> add Alias1 to aliases also
			if alias_variant_1st.count(" ") > 0:
				alias_variants.append(
					"{} {}".format(
						alias_variant_1st.rsplit(" ", 1)[0], alias_variant_2nd
					)
				)  # Name Surname1 / Surname2 -> add Name Surname2 to aliases also
			else:
				alias_variants.append(
					alias_variant_2nd
				)  # Alias1 / Alias2 -> add Alias2 to aliases also
		return alias_variants

	def get_aliases(self, alias, marked_czech=False, nametype=None):
		"""
		Převádí alternativní pojmenování do jednotného formátu.

		Parametry:
		alias - alternativní pojmenování entity (str)
		marked_czech - entita explicitně definovaná jako česká
		"""
		# Eliminating of an alias identical with a title is now contraproductive, 
		# 'cause we need ensure that first alias is in czech language (it is eliminated in serializing step).
		if alias.strip() == "{{PAGENAME}}":
			return
		re_lang_aliases = re.compile(
			"{{(?:Cj|Cizojazyčně|Vjazyce2)\|(?:\d=)?(\w+)\|(?:\d=)?([^}]+)}}",
			flags=re.I,
		)
		re_lang_aliases2 = re.compile("{{Vjazyce\|(\w+)}}\s+([^{]{2}.+)", flags=re.I)
		lang_aliases = re_lang_aliases.findall(alias)
		lang_aliases += re_lang_aliases2.findall(alias)
		alias = re.sub(r"\s+", " ", alias).strip()
		alias = re.sub(r"\s*<hr\s*/>\s*", "", alias)
		alias = alias.strip(",")
		alias = re.sub(r"(?:'')", "", alias)
		alias = re.sub(r"(?:,{2,}|;)\s*", ALIASES_SEPARATOR, alias)
		#        alias = re.sub(r"\s+/\s+", ", ", alias) # commented / deactivated due to Ludvík z Pruska
		alias = re.sub(r"\s*<hiero>.*</hiero>\s*", "", alias, flags=re.I)
		alias = re.sub(r"\s*{{Poznámka pod čarou.*(?:}})?\s*$", "", alias, flags=re.I)
		alias = re.sub(r"\s*\{{Unicode\|([^}]+)}}\s*", r" \1", alias, flags=re.I)
		alias = re.sub(
			r"\s*\({{(?:Cj|Cizojazyčně)\|(?:\d=)?\w+\|(?:\d=)?[^}]+}}\)\s*",
			"",
			alias,
			flags=re.I,
		)  # aliases are covered by "lang_aliases"
		alias = re.sub(
			r"\s*{{(?:Cj|Cizojazyčně)\|(?:\d=)?\w+\|(?:\d=)?[^}]+}}\s*",
			"",
			alias,
			flags=re.I,
		)  # aliases are covered by "lang_aliases"
		alias = re.sub(
			r"\s*\({{V ?jazyce2\|\w+\|[^}]+}}\)\s*", "", alias, flags=re.I
		)  # aliases are covered by "lang_aliases"
		alias = re.sub(
			r"\s*\(?{{V ?jazyce\|\w+}}\)?:?\s*", "", alias, flags=re.I
		)  # aliases are covered by "lang_aliases"
		alias = re.sub(
			r"\s*\(?{{(?:Jaz|Jazyk)\|[\w-]+\|([^}]+)}}\)?:?\s*",
			r"\1",
			alias,
			flags=re.I,
		)
		alias = re.sub(r"\s*{{(?:Malé|Velké)\|(.*?)}}\s*", r"\1", alias, flags=re.I)
		if re.search(r"\s*{{Možná hledáte", alias, flags=re.I):
			alias = re.sub(
				r"\s*{{Možná hledáte|([^=|])*?}}\s*", r"\1", alias, flags=re.I
			)
			alias = re.sub(
				r"\s*{{Možná hledáte|.*?jiné\s*=\s*([^|])*?.*?}}\s*",
				r"\1",
				alias,
				flags=re.I,
			)
		# TODO: přidat šablonu přesměrování
		alias = re.sub(r"\s*{{[a-z]{2}}};?\s*", "", alias)
		alias = re.sub(r"\s*\[[^]]+\]\s*", "", alias)
		alias = re.sub(r",(?!\s)", ALIASES_SEPARATOR, alias)
		alias = alias.replace(",|", "|")
		alias = re.sub(r"[\w\s\-–—−,.()]+:\s*\|?", "", alias)
		alias = re.sub(r"\s*\([^)]+\)\s*", " ", alias)
		alias = alias.strip(",")
		alias = re.sub(r"\|{2,}", "|", alias)
		alias = re.sub(r"^(\s*\|\s*)+$", "", alias)
		alias = self.custom_transform_alias(alias)
		alias = re.sub(
			r"^viz(\.|\s)", "", alias
		)  # vyhození navigačního slova "viz" - například "viz něco" -> "něco"
		alias = re.sub(
			r"{{[^}]+?}}", "", alias
		)  # vyhození ostatních šablon (nové šablony by dělaly nepořádek)
		alias = re.sub(r"[()\[\]{}]", "", alias)
		alias = re.sub(r"<.*?>", "", alias)
		alias = re.sub(r"[„“”]", '"', alias)  # quotation unification

		result = DictOfUniqueDict()

		for a in alias.split("|"):
			a = a.strip()
			for av in self.unfold_alias_variants(a):
				if re.search(r"[^\W_/]", av):
					if marked_czech:
						result.update(
							self.scrape_quoted_inside(av, nametype, self.LANG_CZECH)
						)
						self.n_marked_czech += 1

					else:
						if self.first_alias is None and nametype is None:
							self.first_alias = av
						result.update(self.scrape_quoted_inside(av, nametype))

		for lng, a in lang_aliases:
			a = a.strip()
			for av in self.unfold_alias_variants(a):
				# TODO: maybe, it is needed custom_transform_alias()?
				if re.search(r"[^\W_]", av):
					if not len(self.aliases):
						self.first_alias = av
					result.update(self.scrape_quoted_inside(av, nametype, lng))

		return result

	def scrape_quoted_inside(self, alias, nametype, lang=None):
		result = DictOfUniqueDict()

		if not alias.startswith('"') or not alias.endswith('"'):
			result[alias] = self.get_alias_properties(nametype, lang)

		quotedNames = []
		while True:
			quotedName = re.search(r"(?P<quote>[\"])(.+?)(?P=quote)", alias)

			if quotedName:
				if not regex.match(
					"^\p{Lu}\.(\s*\p{Lu}\.)+$", quotedName.group(2)
				):  # Elimination of initials like "V. H."
					quotedNames.append(quotedName.group(2))
				alias = re.sub(re.escape(quotedName.group(0)), "", alias)
			else:
				break

		if len(quotedNames):
			for qn in quotedNames:
				result[qn] = self.get_alias_properties(self.NTYPE_QUOTED, lang)

			result[alias] = self.get_alias_properties(nametype, lang)

		return result

	def get_alias_properties(self, nametype, lang=None):
		return {KEY_LANG: lang, self.KEY_NAMETYPE: nametype}

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
		self.aliases.update(self.aliases_infobox_cz)
		self.aliases.update(self.aliases_infobox)

		if (
			self.n_marked_czech == 0
			and self.first_alias
			and len(self.aliases.keys()) > 0
		):
			self.aliases[self.first_alias][KEY_LANG] = self.LANG_CZECH

		self.aliases.pop(self.title, None)

		preserialized = set()
		for alias, properties in self.aliases.items():
			tmp_flags = ""
			for key, value in properties.items():
				#                preserialized.add(alias + "#lang=" + (self.LANG_CZECH if (possible_czech and lang in [None, self.LANG_CZECH]) else (lang if lang != None else LANG_UNKNOWN)))
				if key == KEY_LANG and value is None:
					value = LANG_UNKNOWN
				if key != self.KEY_NAMETYPE or value is not None:
					tmp_flags += "#" + key + "=" + value
			preserialized.add(alias + tmp_flags)

		return "|".join(preserialized)

	def extract_images(self):
		keys = ["obrázek", "vlajka", "znak", "mapa umístění", "mapa_umítění", "mapa", "logo"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_image(value)

	def process_and_clean_common_images(self, line):
		"""
		Process common image, transform it to Wikimedia Commons absolute path and return the rest of line without this common image

		Parameters:
		* line - input line of wiki page (str)
		"""

		retval = False
		images = re.findall(
			r"(\[\[(?:Soubor|File):([^|]+?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg))(?:\|(?:[^\[\]]|\[\[[^\]]+\]\]|(?<!\[)\[[^\[\]]+\])*)*\]\])",
			line,
			re.I,
		)
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

		image = re.sub(
			r"{{.*$", "", image
		)  # remove templates with descriptions from image path
		image = (
			re.sub(r"\s*\|.*$", "", image).replace("}", "").strip().replace(" ", "_")
		)
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
		pass

