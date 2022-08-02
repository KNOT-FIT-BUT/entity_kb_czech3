
import re
from ent_core import EntCore


class EntCountry(EntCore):
	
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		
		super(EntCountry, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.latitude = ""
		self.longitude = ""
		self.area = ""
		self.population = ""

		self.get_wiki_api_location(title)

	##
	# @brief serializes entity data for output (tsv format)
	# @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			str(self.latitude),
			str(self.longitude),
			self.area,
			self.population
		]
		return self.serialize("\t".join(data))

	def assign_values(self):

		self.assign_prefix()
		self.assign_aliases()

		# data extraction from infobox
		self.assign_area()
		self.assign_population()

		# sentence / text extraction
		self.extract_text()

		pass

	def assign_prefix(self):
		# prefix - zaniklé státy
		content = "\n".join(self.categories)
		if re.search(r"Krátce\s+existující\s+státy|Zaniklé\s+(?:státy|monarchie)", content, re.I,):
			self.prefix = "country:former"
		
	def assign_aliases(self):
		# aliases - czech name is preferable
		keys = ["název česky", "název_česky"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.del_redundant_text(self.infobox_data[key])
				self.aliases_infobox_cz.update(self.get_aliases(value, marked_czech=True))
				
				if len(self.aliases_infobox):
					self.aliases_infobox_orig.update(self.aliases_infobox)
					self.aliases_infobox.clear()
					if not len(self.aliases):
						self.first_alias = None
				break

		# aliases - common name may contain name in local language
		key = "název"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.del_redundant_text(self.infobox_data[key])
			aliases = self.get_aliases(value)
			
			if len(self.aliases_infobox_cz):
				var_aliases = self.aliases_infobox_orig
				if not len(self.aliases):
					self.first_alias = None
			else:
				var_aliases = self.aliases_infobox
			var_aliases.update(aliases)

		# jazyk pro oficiální nečeský název
		key = "iso2"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.infobox_data[key]
			self.lang_orig = value.lower()

	def assign_area(self):
		# rozloha
		keys = ["rozloha", "výměra"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_area(self.del_redundant_text(value))
				break

	def assign_population(self):
		# počet obyvatel
		key = "obyvatel"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.infobox_data[key]
			self.get_population(self.del_redundant_text(value))

	def extract_text(self):
		# první věta
		abbrs = "".join(
			(
				r"(?<!\s(?:tzv|at[dp]))",
				r"(?<!\s(?:apod|(?:ku|na|po)př|příp))",
				r"(?<!\s(?:[amt]j|fr))",
				r"(?<!\d)",
			)
		)
		rexp = re.search(
			r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|nacház(?:í|ejí)|patř(?:í|il)|stal|rozprostír|lež(?:í|el)).*?"
			+ abbrs
			+ "\.(?![^[]*?\]\])",
			self.first_paragraph,
		)
		
		if rexp:
			if not self.description:
				self.get_first_sentence(self.del_redundant_text(rexp.group(0), ", "))

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
			# extrakce z 1. věty: Česká republika (Czech Republic) je ...
			fs_aliases = re.findall(
				re.escape(self.title) + r"\s+\((.+?)\)", rexp.group(0)
			)
			if fs_aliases:
				for fs_alias in fs_aliases:
					self.aliases.update(
						self.get_aliases(self.del_redundant_text(fs_alias))
					)
			fs_aliases = re.search(
				r"(?:\s+někdy)?\s+(?:označovan[áéý]|označován[ao]?|nazývan[áéý]|nazýván[ao]?)(?:\s+(?:(?:(?:i|také)\s+)?jako)|i|také)?\s+(''.+?''|{{.+?}})(.+)",
				rexp.group(0),
			)
			if fs_aliases:
				self.aliases.update(
					self.get_aliases(
						self.del_redundant_text(fs_aliases.group(1)).strip("'")
					)
				)
				fs_next_aliases = re.finditer(
					r"(?:,|\s+nebo)(?:\s+(?:(?:(?:i|také)\s+)?jako)|i|také)?\s+(''.+?''|{{.+?}})",
					fs_aliases.group(2),
				)
				for fs_next_alias in fs_next_aliases:
					self.aliases.update(self.get_aliases(self.del_redundant_text(fs_next_alias.group(1).strip("'"))))

	def custom_transform_alias(self, alias):
		"""
		Vlastní transformace aliasu.

		Parametry:
		alias - alternativní pojmenování entity (str)
		"""

		return self.transform_geo_alias(alias)

	def get_first_sentence(self, fs):
		"""
		Převádí první větu stránky do jednotného formátu a získává z ní popis.

		Parametry:
		fs - první věta stránky (str)
		"""
		# TODO: refactorize
		fs = re.sub(
			r"{{(?:vjazyce2|cizojazyčně|audio|cj|jazyk)\|.*?\|(.+?)}}",
			r"\1",
			fs,
			flags=re.I,
		)
		fs = re.sub(r"{{IPA\d?\|(.+?)}}", r"\1", fs, flags=re.I)
		fs = re.sub(r"{{výslovnost\|(.+?)\|.*?}}", r"", fs, flags=re.I)
		fs = re.sub(
			r"{{čínsky(.+?)}}",
			lambda x: re.sub(
				"(?:znaky|pchin-jin|tradiční|zjednodušené|pinyin)"
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
		fs = fs.replace("''", "").replace(")", "").replace("|group=pozn.}}", "")

		self.description = fs

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