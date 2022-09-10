
import re
from lang_modules.cs.core_utils import CoreUtils

class SettlementUtils:

	KEYWORDS = {
		"population": ["počet obyvatel", "počet_obyvatel", "pocet obyvatel", "pocet_obyvatel"],
		"country": ["země", "stát"]
	}
	
	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	# ##
	# # @brief Převádí rozlohu sídla do jednotného formátu.
	# # @param area - rozloha/výměra sídla (str)
	# def get_area(self, area):
	# 	area = re.sub(r"\(.*?\)", "", area)
	# 	area = re.sub(r"\[.*?\]", "", area)
	# 	area = re.sub(r"<.*?>", "", area)
	# 	area = re.sub(r"{{.*?}}", "", area).replace("{", "").replace("}", "")
	# 	area = re.sub(r"(?<=\d)\s(?=\d)", "", area).strip()
	# 	area = re.sub(r"(?<=\d)\.(?=\d)", ",", area)
	# 	area = re.sub(r"^\D*(?=\d)", "", area)
	# 	area = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", area)
	# 	area = "" if not re.search(r"\d", area) else area

	# 	return area

	# ##
	# # @brief Převádí stát, ke kterému sídlo patří, do jednotného formátu.
	# # @param country - země, ke které sídlo patří (str)
	# def get_country(self, country):	
	# 	country = re.sub(r"{{vlajka\s+a\s+název\|(.*?)}}", r"\1", country, flags=re.I)
	# 	country = re.sub(r"{{.*?}}", "", country)
	# 	country = (
	# 		"Česká republika"
	# 		if re.search(r"Čechy|Morava|Slezsko", country, re.I)
	# 		else country
	# 	)
	# 	country = re.sub(r",?\s*\(.*?\)", "", country)
	# 	country = re.sub(r"\s+", " ", country).strip().replace("'", "")

	# 	return country

	# ##
	# # @brief Převádí počet obyvatel sídla do jednotného formátu.
	# # @param population - počet obyvatel sídla (str)
	# def get_population(self, population):
	# 	coef = (
	# 		1000000
	# 		if re.search(r"mil\.|mili[oó]n", population, re.I)
	# 		else 1000
	# 		if re.search(r"tis\.|tis[ií]c", population, re.I)
	# 		else 0
	# 	)

	# 	population = re.sub(r"\(.*?\)", "", population)
	# 	population = re.sub(r"\[.*?\]", "", population)
	# 	population = re.sub(r"<.*?>", "", population)
	# 	population = (
	# 		re.sub(r"{{.*?}}", "", population).replace("{", "").replace("}", "")
	# 	)
	# 	population = re.sub(r"(?<=\d)[,.\s](?=\d)", "", population).strip()
	# 	population = re.sub(r"^\D*(?=\d)", "", population)
	# 	population = re.sub(r"^(\d+)\D.*$", r"\1", population)
	# 	population = "" if not re.search(r"\d", population) else population

	# 	if coef and population:
	# 		population = str(int(population) * coef)

	# 	return population

