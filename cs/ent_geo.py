
import re
from ent_core import EntCore

class EntGeo(EntCore):

	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):

		super(EntGeo, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.area = ""
		self.continent = ""
		self.latitude = ""
		self.longitude = ""
		self.population = ""
		self.total_height = ""

	##
	# @brief serializes entity data for output (tsv format)
	# @return tab separated values containing all of entity data <string>
	def __repr__(self):

		data = []

		if self.prefix in ["geo:island", "geo:waterfall", "geo:relief"]:
			data += [self.continent]

		data += [
			str(self.latitude),
			str(self.longitude),
		]

		if self.prefix in ["geo:continent", "geo:island"]:
			data += [self.area, self.population]
		elif self.prefix == "geo:waterfall":
			data += [self.total_height]

		return self.serialize("\t".join(data))

	def assign_values(self):
		
		self.assign_prefix()

		self.get_wiki_api_location(self.title)
		self.assign_coordinates()
		
		if self.prefix == "geo:waterfall":
			self.assign_total_height()
		
		if self.prefix in ["geo:island", "geo:continent"]:
			self.assign_area()
			self.assign_population()

		if self.prefix in ["geo:waterfall", "geo:island", "geo:relief"]:
			self.assign_continent()

		self.extract_text()

	def assign_prefix(self):
		
		if (re.search(r"poloostrovy\s+(?:na|ve?)", "\n".join(self.categories), re.I)
				or re.search(r"poloostrov", self.original_title, re.I)):
			self.prefix = "geo:peninsula"
		elif (self.infobox_name in ["reliéf", "hora", "průsmyk", "pohoří", "sedlo"] 
				or re.search(r"reliéf|hora|průsmyk|pohoří|sedlo", self.original_title, re.I)):
			self.prefix = "geo:relief"
		elif (self.infobox_name == "kontinent"
				or re.search(r"kontinent", self.original_title, re.I)):
			self.prefix = "geo:continent"
		elif (self.infobox_name == "ostrov"
				or re.search(r"ostrov", self.original_title, re.I)):
			self.prefix = "geo:island"
		elif (self.infobox_name == "vodopád"
				or re.search(r"vodopád", self.original_title, re.I)):
			self.prefix = "geo:waterfall"
		else:
			self.prefix = "geo:unknown"

	def assign_coordinates(self):
		# zeměpisná šířka
		keys = ["zeměpisná šířka", "zeměpisná_šířka"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_latitude(self.del_redundant_text(value))
				break

		# zeměpisná délka
		keys = ["zeměpisná délka", "zeměpisná_délka"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_longitude(self.del_redundant_text(value))
				break

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

	def assign_population(self):
		# počet obyvatel
		keys = ["počet obyvatel", "počet_obyvatel"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_population(self.del_redundant_text(value))
				break
		
	def assign_total_height(self):
		keys = ["celková výška", "celková_výška"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				self.get_total_height(self.del_redundant_text(value))
				break

	def assign_aliases(self):
		# aliasy
		keys = ["název", "jméno"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.del_redundant_text(self.infobox_data[key])
				self.aliases_infobox.update(self.get_aliases(value))
				break

		keys = ["název místním jazykem", "název_místním_jazykem"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.del_redundant_text(self.infobox_data[key])
				self.aliases_infobox_orig.update(self.get_aliases(value))
				if not len(self.aliases) and not len(self.aliases_infobox):
					self.first_alias = None	
				break

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
				r"(?<!nad m|ev\.\sč)",
			)
		)
		rexp = re.search(
			r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|nacház(?:í|ejí)|patř(?:í|il)|stal|rozprostír|lež(?:í|el)).*?(?:"
			+ abbrs
			+ "\.(?!(?:[^[]*?\]\]|\s*[a-z]))|\.$)",
			content,
		)
		if rexp:
			if not self.description:
				self.get_first_sentence(self.del_redundant_text(rexp.group(0), ", "))

			tmp_first_sentence = rexp.group(0)
			fs_aliases_lang_links = []
			# extrakce alternativních pojmenování z první věty
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
		Převádí rozlohu geografické entity do jednotného formátu.

		Parametry:
		area - rozloha geografické entity v kilometrech čtverečních (str)
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
		Převádí světadíl, na kterém se geografická entita nachází, do jednotného formátu.

		Parametry:
		continent - světadíl, na kterém se geografická entita nachází (str)
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

	def get_population(self, population):
		"""
		Převádí počet obyvatel, jenž žije na území geografické entity, do jednotného formátu.

		Parametry:
		population - počet obyvatel, jenž žije na území geografické entity (str)
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
		population = (
			"0"
			if re.search(r"neobydlen|bez.+?obyvatel", population, re.I)
			else population
		)  # pouze v tomto souboru
		population = "" if not re.search(r"\d", population) else population

		if coef and population:
			population = str(int(population) * coef)

		self.population = population

	def get_total_height(self, height):
		"""
		Převádí celkovou výšku vodopádu do jednotného formátu.

		Parametry:
		height - ceková výška vodopádu (str)
		"""
		height = re.sub(r"\(.*?\)", "", height)
		height = re.sub(r"\[.*?\]", "", height)
		height = re.sub(r"<.*?>", "", height)
		height = re.sub(r"{{.*?}}", "", height).replace("{", "").replace("}", "")
		height = re.sub(r"(?<=\d)\s(?=\d)", "", height).strip()
		height = re.sub(r"(?<=\d)\.(?=\d)", ",", height)
		height = re.sub(r"^\D*(?=\d)", "", height)
		height = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", height)
		height = "" if not re.search(r"\d", height) else height

		self.total_height = height
