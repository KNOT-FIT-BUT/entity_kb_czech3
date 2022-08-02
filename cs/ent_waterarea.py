
import re
from ent_core import EntCore


class EntWaterArea(EntCore):

	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):

		super(EntWaterArea, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.latitude = ""
		self.longitude = ""
		self.area = ""
		self.continent = ""

	##
	# @brief serializes entity data for output (tsv format)
	# @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.continent,
			str(self.latitude),
			str(self.longitude),
			self.area
		]
		return self.serialize("\t".join(data))

	def assign_values(self):
		
		self.assign_aliases()

		self.get_wiki_api_location(self.title)
		self.assign_continent()
		self.assign_coordinates()
		self.assign_area()

		self.extract_text()

	def assign_continent(self):
		# světadíl
		key = "světadíl"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.infobox_data[key]
			self.get_continent(self.del_redundant_text(value))

	def assign_area(self):
		# rozloha
		key = "rozloha"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.infobox_data[key]
			self.get_area(self.del_redundant_text(value))
	
	def assign_coordinates(self):
		# zeměpisná šířka
		keys = ["zeměpisná šířka", "zeměpisná_šířka"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_latitude(self.del_redundant_text(value))

		# zeměpisná výška
		keys = ["zeměpisná výška", "zeměpisná_výška"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_longitude(self.del_redundant_text(value))

	def assign_aliases(self):
		# aliasy
		key = "název"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.del_redundant_text(self.infobox_data[key])
			self.aliases_infobox.update(self.get_aliases(value))			

	def extract_text(self):
		# první věta

		content = self.first_paragraph
		content = content.replace("&nbsp;", " ")
		content = re.sub(r"m\sn\.\s*", "metrů nad ", content)

		abbrs = "".join(
			(
				r"(?<!\s(?:tzv|at[pd]))",
				r"(?<!\s(?:apod|(?:ku|na|po)př|příp))",
				r"(?<!\s(?:[amt]j|fr))",
				r"(?<!\d)",
				r"(?<!nad m|ev\.\sč)",
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
		Převádí rozlohu vodní plochy do jednotného formátu.

		Parametry:
		area - rozloha vodní plochy v kilometrech čtverečních (str)
		"""
		is_ha = re.search(r"\d\s*(?:ha|hektar)", area, re.I)

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
				area = str(float(area.replace(",", ".")) / 100).replace(".", ",")
			except ValueError:
				pass

		self.area = area

	def get_continent(self, continent):
		"""
		Převádí světadíl, na kterém se vodní plocha nachází, do jednotného formátu.

		Parametry:
		continent - světadíl, na kterém se vodní plocha nachází (str)
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
			r"{{(?:cj|cizojazyčně|vjazyce\d?)\|\w+\|(.*?)}}", r"\1", fs, flags=re.I
		)
		fs = re.sub(r"{{PAGENAME}}", self.title, fs, flags=re.I)
		fs = re.sub(r"{{.*?}}", "", fs).replace("{", "").replace("}", "")
		fs = re.sub(r"/.*?/", "", fs)
		fs = re.sub(r"\s+", " ", fs).strip()
		fs = re.sub(r"^\s*}}", "", fs)  # Eliminate the end of a template
		fs = re.sub(r"[()<>\[\]{}/]", "", fs).replace(" ,", ",").replace(" .", ".")

		self.description = fs