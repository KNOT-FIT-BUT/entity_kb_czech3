
import re, regex, requests
from lang_modules.cs.libs.DictOfUniqueDict import *
from lang_modules.cs.libs.UniqueDict import KEY_LANG, LANG_ORIG, LANG_UNKNOWN

ALIASES_SEPARATOR = re.escape(", ")
KEY_NAMETYPE = "ntype"
LANG_CZECH = "cs"
NTYPE_QUOTED = "quoted"

WIKI_API_URL = "https://cs.wikipedia.org/w/api.php"
WIKI_API_PARAMS_BASE = {
	"action": "query",
	"format": "json",
}

class CoreUtils:

	DISAMBIG_PATTERN = r"{{[^}]*?(?:rozcestník)(?:\|[^}]*?)?}}"
	CATEGORY_PATTERN = r"\[\[Kategorie:\s?(.*?)\]\]"

	# lang specific keywords
	KEYWORDS = {
		"image": 		["obrázek", "vlajka", "znak", "mapa umístění", "mapa_umítění", "mapa", "logo"],
		"area_km2": 	["rozloha", "výměra", "plocha"],
		"area_sqmi": 	[],
		"area_other": 	[]
	}

	@staticmethod
	def is_entity(title):
		# speciální stránky Wikipedie nepojednávají o entitách
		if title.startswith(
			(
				"wikipedie:",
				"redaktor:",
				"soubor:",
				"mediawiki:",
				"šablona:",
				"pomoc:",
				"kategorie:",
				"speciální:",
				"portál:",
				"modul:",
				"seznam",
				"geografie",
				"společenstvo",
			)
		):
			return False

		# stránky pro data (datumy) nepojednávají o entitách
		if re.search(r"^\d{1,2}\. [^\W\d_]+$", title):
			return False

		# ostatní stránky mohou pojednávat o entitách
		return True

	##
	# @brief Odstraňuje přebytečné části textu, ale pouze ty, které jsou společné pro všechny získávané údaje.
	# @param text - text, který má být upraven (str)
	# @param multiple_separator - znak oddělující více řádků
	# @param clear_name_links - odstraňuje odkazy z názvů
	# @return Upravený text. (str)
	@staticmethod
	def del_redundant_text(text, multiple_separator="|", langmap=dict()):
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

	# TODO: fix this
	@classmethod
	def assign_coordinates(cls, entity):
		latitude = ""
		longitude = ""

		# zeměpisná šířka
		keys = ["zeměpisná šířka", "zeměpisná_šířka"]
		for key in keys:
			if key in entity.infobox_data and entity.infobox_data[key]:
				value = entity.infobox_data[key]
				latitude = cls.get_latitude(cls.del_redundant_text(value))
				break

		# zeměpisná výška
		keys = ["zeměpisná výška", "zeměpisná_výška"]
		for key in keys:
			if key in entity.infobox_data and entity.infobox_data[key]:
				value = entity.infobox_data[key]
				longitude = cls.get_longitude(cls.del_redundant_text(value))
				break

		if latitude and longitude:
			return (latitude, longitude)
		else:
			return cls.get_wiki_api_location(entity.title)

	@staticmethod
	def get_wiki_api_location(title):
		wiki_api_params = WIKI_API_PARAMS_BASE.copy()
		wiki_api_params["prop"] = "coordinates"
		wiki_api_params["titles"] = title
		try:
			r = requests.get(WIKI_API_URL, params=wiki_api_params)
			pages = r.json()["query"]["pages"]
			first_page = next(iter(pages))
			if first_page != "-1":
				latitude = pages[first_page]["coordinates"][0]["lat"]
				longitude = pages[first_page]["coordinates"][0]["lon"]
				return (str(latitude), str(longitude))
		except Exception as e:
			return ("", "")

	##
	# @brief Převádí zeměpisnou šířku geografické entity do jednotného formátu.
	# @param latitude - zeměpisná šířka geografické entity (str)
	@staticmethod
	def get_latitude(latitude):
		latitude = re.sub(r"\(.*?\)", "", latitude)
		latitude = re.sub(r"\[.*?\]", "", latitude)
		latitude = re.sub(r"<.*?>", "", latitude)
		latitude = re.sub(r"{{.*?}}", "", latitude).replace("{", "").replace("}", "")
		latitude = re.sub(r"(?<=\d)\s(?=\d)", "", latitude).strip()
		latitude = re.sub(r"(?<=\d)\.(?=\d)", ",", latitude)
		latitude = re.sub(r"^[^\d-]*(?=\d)", "", latitude)
		latitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", latitude)
		latitude = "" if not re.search(r"\d", latitude) else latitude

		return latitude

	##
	# @brief Převádí zeměpisnou délku geografické entity do jednotného formátu.
	# @param longitude - zeměpisná délka geografické entity (str)
	@staticmethod
	def get_longitude(longitude):
		longitude = re.sub(r"\(.*?\)", "", longitude)
		longitude = re.sub(r"\[.*?\]", "", longitude)
		longitude = re.sub(r"<.*?>", "", longitude)
		longitude = re.sub(r"{{.*?}}", "", longitude).replace("{", "").replace("}", "")
		longitude = re.sub(r"(?<=\d)\s(?=\d)", "", longitude).strip()
		longitude = re.sub(r"(?<=\d)\.(?=\d)", ",", longitude)
		longitude = re.sub(r"^[^\d-]*(?=\d)", "", longitude)
		longitude = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", longitude)
		longitude = "" if not re.search(r"\d", longitude) else longitude

		return longitude

	##
	# @brief Převádí alternativní pojmenování do jednotného formátu.
	# @param alias - alternativní pojmenování entity (str)
	# @param marked_czech - entita explicitně definovaná jako česká
	@classmethod
	def get_aliases(cls, alias, aliases, custom_transform_alias, custom_data, marked_czech=False, nametype=None):		
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
		
		# TODO: make sure this works
		alias = custom_transform_alias(alias, custom_data)
		
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
		n_marked_czech = 0
		first_alias = None

		for a in alias.split("|"):
			a = a.strip()
			for av in cls.unfold_alias_variants(a):
				if re.search(r"[^\W_/]", av):
					if marked_czech:
						result.update(
							cls.scrape_quoted_inside(av, nametype, LANG_CZECH)
						)
						n_marked_czech += 1
					else:
						if first_alias is None and nametype is None:
							first_alias = av
						result.update(cls.scrape_quoted_inside(av, nametype))

		for lng, a in lang_aliases:
			a = a.strip()
			for av in cls.unfold_alias_variants(a):
				# TODO: maybe, it is needed custom_transform_alias()?
				if re.search(r"[^\W_]", av):
					if not len(aliases):
						first_alias = av
					result.update(cls.scrape_quoted_inside(av, nametype, lng))

		return (result, n_marked_czech, first_alias)

	@classmethod
	def scrape_quoted_inside(cls, alias, nametype, lang=None):
		result = DictOfUniqueDict()

		if not alias.startswith('"') or not alias.endswith('"'):
			result[alias] = cls.get_alias_properties(nametype, lang)

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
				result[qn] = cls.get_alias_properties(NTYPE_QUOTED, lang)

			result[alias] = cls.get_alias_properties(nametype, lang)

		return result

	@staticmethod
	def get_alias_properties(nametype, lang=None):
		return {KEY_LANG: lang, KEY_NAMETYPE: nametype}

	@staticmethod
	def unfold_alias_variants(alias):
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

	##
	# @brief Serialized aliases to be written while creating KB
	#
	# changes were made to unify languages
	@staticmethod
	def serialize_aliases(aliases, title, n_marked_czech, first_alias):

		if (n_marked_czech == 0 and first_alias and len(aliases.keys()) > 0):
			aliases[first_alias][KEY_LANG] = LANG_CZECH

		aliases.pop(title, None)

		preserialized = set()
		for alias, properties in aliases.items():
			tmp_flags = ""
			for key, value in properties.items():
				if key == KEY_LANG and value is None:
					value = LANG_UNKNOWN
				if key != KEY_NAMETYPE or value is not None:
					tmp_flags += f"#{key}={value}"
			preserialized.add(alias + tmp_flags)

		return "|".join(preserialized)
