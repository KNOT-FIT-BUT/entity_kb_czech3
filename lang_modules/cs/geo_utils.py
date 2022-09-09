
import re
from lang_modules.cs.core_utils import CoreUtils

class GeoUtils:

	KEYWORDS = {
		"height": ["celková výška", "celková_výška"]
	}
	
	@staticmethod
	def assign_prefix(geo):
		if (re.search(r"poloostrovy\s+(?:na|ve?)", "\n".join(geo.categories), re.I)
				or re.search(r"poloostrov", geo.original_title, re.I)):
			return "geo:peninsula"
		elif (geo.infobox_name in ["reliéf", "hora", "průsmyk", "pohoří", "sedlo"] 
				or re.search(r"reliéf|hora|průsmyk|pohoří|sedlo", geo.original_title, re.I)):
			return "geo:relief"
		elif (geo.infobox_name == "kontinent"
				or re.search(r"kontinent", geo.original_title, re.I)):
			return "geo:continent"
		elif (geo.infobox_name == "ostrov"
				or re.search(r"ostrov", geo.original_title, re.I)):
			return "geo:island"
		elif (geo.infobox_name == "vodopád"
				or re.search(r"vodopád", geo.original_title, re.I)):
			return "geo:waterfall"
		else:
			return "geo:unknown"

	@staticmethod
	def get_coef(value):
		if re.search(r"mil\.|mili[oó]n", value, re.I):
			return 10e6
		if re.search(r"tis\.|tis[ií]c", value, re.I):
			return 10e3
		return 1

	@classmethod
	def assign_population(cls, infobox_data):
		population = ""
		# počet obyvatel
		keys = ["počet obyvatel", "počet_obyvatel"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				population = cls.get_population(CoreUtils.del_redundant_text(value))
				break
		return population
		
	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	# ##
	# # @brief Převádí rozlohu geografické entity do jednotného formátu.
	# # @param area - rozloha geografické entity v kilometrech čtverečních (str)
	# @staticmethod
	# def get_area(area):
	# 	is_ha = re.search(r"\d\s*(?:ha|hektar)", area, re.I)

	# 	area = re.sub(r"\(.*?\)", "", area)
	# 	area = re.sub(r"\[.*?\]", "", area)
	# 	area = re.sub(r"<.*?>", "", area)
	# 	area = re.sub(r"{{.*?}}", "", area).replace("{", "").replace("}", "")
	# 	area = re.sub(r"(?<=\d)\s(?=\d)", "", area).strip()
	# 	area = re.sub(r"(?<=\d)\.(?=\d)", ",", area)
	# 	area = re.sub(r"^\D*(?=\d)", "", area)
	# 	area = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", area)
	# 	area = "" if not re.search(r"\d", area) else area

	# 	if (
	# 		is_ha
	# 	):  # je-li údaj uveden v hektarech, dojde k převodu na kilometry čtvereční
	# 		try:
	# 			area = str(float(area.replace(",", ".")) / 100).replace(".", ",")
	# 		except ValueError:
	# 			pass

	# 	return area

	##
	# Převádí počet obyvatel, jenž žije na území geografické entity, do jednotného formátu.
	# population - počet obyvatel, jenž žije na území geografické entity (str)
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
		population = (
			"0"
			if re.search(r"neobydlen|bez.+?obyvatel", population, re.I)
			else population
		)  # pouze v tomto souboru
		population = "" if not re.search(r"\d", population) else population

		if coef and population:
			population = str(int(population) * coef)

		return population

	# ##
	# # @brief Převádí celkovou výšku vodopádu do jednotného formátu.
	# # @param height - ceková výška vodopádu (str)
	# @staticmethod
	# def get_total_height(height):
	# 	height = re.sub(r"\(.*?\)", "", height)
	# 	height = re.sub(r"\[.*?\]", "", height)
	# 	height = re.sub(r"<.*?>", "", height)
	# 	height = re.sub(r"{{.*?}}", "", height).replace("{", "").replace("}", "")
	# 	height = re.sub(r"(?<=\d)\s(?=\d)", "", height).strip()
	# 	height = re.sub(r"(?<=\d)\.(?=\d)", ",", height)
	# 	height = re.sub(r"^\D*(?=\d)", "", height)
	# 	height = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", height)
	# 	height = "" if not re.search(r"\d", height) else height

	# 	return height
