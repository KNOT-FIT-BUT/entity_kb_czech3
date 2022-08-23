
import re
from core_utils import CoreUtils

class SettlementUtils:

	@classmethod
	def extract_infobox(cls, ent_data, debugger):
		extraction = {
			"country": "",
			"latitude": "",
			"longitude": "",
			"area": "",
			"population": ""
		}

		infobox_name, infobox_data, title = (
			ent_data["infobox_name"],
			ent_data["infobox_data"],
			ent_data["title"]
		)

		extraction["latitude"], extraction["longitude"] = CoreUtils.get_wiki_api_location(title)
		extraction["country"] = cls.assign_country(infobox_name, infobox_data)
		extraction["area"] = cls.assign_area(infobox_data)
		extraction["population"] = cls.assign_population(infobox_data)

		return extraction

	@classmethod
	def assign_country(cls, infobox_name, infobox_data):
		country = ""
		
		# země
		keys = ["česká obec", "statutární město"]
		if infobox_name in keys:			
			country = "Česká republika"

		key = "anglické město"
		if infobox_name == key:
			country = "Spojené království"

		keys = ["země", "stát"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				country = cls.get_country(CoreUtils.del_redundant_text(value))				
				break

		return country

	@classmethod
	def assign_area(cls, infobox_data):
		area = ""
		
		# rozloha
		keys = ["rozloha", "výměra"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				area = cls.get_area(CoreUtils.del_redundant_text(value))

		return area

	@classmethod
	def assign_population(cls, infobox_data):
		population = ""

		# počet obyvatel
		keys = ["počet obyvatel", "počet_obyvatel", "pocet obyvatel", "pocet_obyvatel"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				population = cls.get_population(CoreUtils.del_redundant_text(value))
				break
		
		return population
		
	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	##
	# @brief Převádí rozlohu sídla do jednotného formátu.
	# @param area - rozloha/výměra sídla (str)
	def get_area(self, area):
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
	# @brief Převádí stát, ke kterému sídlo patří, do jednotného formátu.
	# @param country - země, ke které sídlo patří (str)
	def get_country(self, country):	
		country = re.sub(r"{{vlajka\s+a\s+název\|(.*?)}}", r"\1", country, flags=re.I)
		country = re.sub(r"{{.*?}}", "", country)
		country = (
			"Česká republika"
			if re.search(r"Čechy|Morava|Slezsko", country, re.I)
			else country
		)
		country = re.sub(r",?\s*\(.*?\)", "", country)
		country = re.sub(r"\s+", " ", country).strip().replace("'", "")

		return country

	##
	# @brief Převádí počet obyvatel sídla do jednotného formátu.
	# @param population - počet obyvatel sídla (str)
	def get_population(self, population):
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

