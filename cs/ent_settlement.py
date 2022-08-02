#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projekt: entity_kb_czech3 (https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3)
Autoři:
	Michal Planička (xplani02)
	Tomáš Volf (ivolf)

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
from ent_core import EntCore


class EntSettlement(EntCore):

	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		
		super(EntSettlement, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.latitude = ""
		self.longitude = ""
		self.area = ""
		self.country = ""
		self.population = ""

	##
	# @brief serializes entity data for output (tsv format)
	# @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			str(self.latitude),
			str(self.longitude),
			self.area,
			self.country,
			self.population
		]
		return self.serialize("\t".join(data))

	def assign_values(self):
		
		self.assign_aliases()

		self.get_wiki_api_location(self.title)
		self.assign_country()
		self.assign_area()
		self.assign_population()

		self.extract_text()

	def assign_country(self):
		# země
		keys = ["česká obec", "statutární město"]
		if self.infobox_name in keys:
			self.country = "Česká republika"
			return

		key = "anglické město"
		if self.infobox_name == key:
			self.country = "Spojené království"
			return

		keys = ["země", "stát"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_country(self.del_redundant_text(value))				
				break

	def assign_area(self):
		# rozloha
		keys = ["rozloha", "výměra"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_area(self.del_redundant_text(value))

	def assign_population(self):
		# počet obyvatel
		keys = ["počet obyvatel", "počet_obyvatel", "pocet obyvatel", "pocet_obyvatel"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_population(self.del_redundant_text(value))

	def assign_aliases(self):
		# aliasy

		key = "jméno"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.del_redundant_text(self.infobox_data[key])
			self.aliases_infobox_cz.update(self.get_aliases(value, marked_czech=True))

		keys = ["název", "jméno"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.del_redundant_text(self.infobox_data[key], langmap=self.langmap)
				self.aliases_infobox.update(self.get_aliases(value))

		keys = ["originální jméno", "originální_jméno"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.del_redundant_text(self.infobox_data[key], langmap=self.langmap)
				self.aliases_infobox_orig.update(self.get_aliases(value))
				if not len(self.aliases) and not len(self.aliases_infobox):
					self.first_alias = None

	def extract_text(self):

		content = self.first_paragraph
		content = content.replace("&nbsp;", " ")
		content = re.sub(r"m\sn\.\s*", "metrů nad ", content)

		abbrs = "".join(
			(
				r"(?<!\s(?:tzv|at[pd]))",
				r"(?<!\s(?:apod|(?:ku|na|po)př|příp))",
				r"(?<!\s(?:[amt]j|fr))",
				r"(?<!\d)",
				r"(?<!nad m)",
			)
		)
		rexp = re.search(
			r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|nacház(?:í|ejí)|patř(?:í|il)|stal|rozprostír|lež(?:í|el)).*?"
			+ abbrs
			+ "\.(?![^[]*?\]\])",
			content,
		)
		if rexp:
			if not self.description:
				self.get_first_sentence(self.del_redundant_text(rexp.group(0), ", "))
			
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
		country = re.sub(r"{{vlajka\s+a\s+název\|(.*?)}}", r"\1", country, flags=re.I)
		country = re.sub(r"{{.*?}}", "", country)
		country = (
			"Česká republika"
			if re.search(r"Čechy|Morava|Slezsko", country, re.I)
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
			r"{{(?:cj|cizojazyčně|vjazyce\d?)\|\w+\|(.*?)}}", r"\1", fs, flags=re.I
		)
		fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
		fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
		fs = re.sub(r"/.*?/", "", fs)
		fs = re.sub(r"\s+", " ", fs).strip()
		fs = re.sub(r"^\s*}}", "", fs)  # Eliminate the end of a template
		fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",")

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
