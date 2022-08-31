
import re

from lang_modules.cs.core_utils import CoreUtils

class CountryUtils:

	@classmethod
	def extract_infobox(cls, ent_data, debugger):
		extracted = {
			"prefix": "",
			"latitude": "",
			"longitude": "",
			"area": "",
			"population": ""
		}

		infobox_data, categories, title = (
			ent_data["infobox_data"],
			ent_data["categories"],
			ent_data["title"]
		)

		extracted["prefix"] = cls.assign_prefix(categories)

		extracted["latitude"], extracted["longitude"] = CoreUtils.get_wiki_api_location(title)
		extracted["area"] = cls.assign_area(infobox_data, debugger)
		extracted["population"] = cls.assign_population(infobox_data)

		return extracted

	@staticmethod
	def assign_prefix(categories):
		# prefix - zaniklé státy
		content = "\n".join(categories)
		if re.search(r"Krátce\s+existující\s+státy|Zaniklé\s+(?:státy|monarchie)", content, re.I,):
			return "country:former"
		
		return "country"
	
	@classmethod
	def assign_area(cls, infobox_data, debugger):
		area = ""
		
		# rozloha
		keys = ["rozloha", "výměra"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				value = CoreUtils.del_redundant_text(value)
				debugger.log_message(value)
				area = cls.get_area(value)
				break

		return area

	@classmethod
	def assign_population(cls, infobox_data):
		population = ""

		# počet obyvatel
		key = "obyvatel"
		if key in infobox_data and infobox_data[key]:
			value = infobox_data[key]
			value = CoreUtils.del_redundant_text(value)
			population = cls.get_population(value)

		return population

	# TODO: aliases
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

	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	##
	# @brief Převádí rozlohu státu do jednotného formátu.
	# @param area - rozloha státu (str)
	@staticmethod
	def get_area(area):
		area = re.sub(r"\(.*?\)", "", area)
		area = re.sub(r"\[.*?\]", "", area)
		area = re.sub(r"<.*?>", "", area)
		area = re.sub(r"{{.*?}}", "", area).replace("{", "").replace("}", "")
		area = re.sub(r"(?<=\d)\s(?=\d)", "", area).strip()
		area = re.sub(r"(?<=\d)\.(?=\d)", ",", area)
		area = re.sub(r"^\D*(?=\d)", "", area)
		area = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", area)
		area = "" if not re.search(r"\d", area) else area
		return area

	##
	# @brief Převádí počet obyvatel státu do jednotného formátu.
	# @param population - počet obyvatel státu (str)
	@staticmethod
	def get_population(population):
		
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

		return population