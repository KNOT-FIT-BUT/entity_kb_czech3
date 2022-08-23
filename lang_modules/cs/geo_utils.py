
import re
from core_utils import CoreUtils

class GeoUtils:

	@classmethod
	def extract_infobox(cls, ent_data, debugger):
		extraction = {
			"prefix": "",
			"continent": "",
			"latitude": "",
			"longitude": "",
			"area": "",
			"population": "",
			"total_height": ""
		}

		infobox_data, infobox_name, categories, original_title = (
			ent_data["infobox_data"],
			ent_data["infobox_name"],
			ent_data["categories"],
			ent_data["original_title"]
		)

		extraction["prefix"] = cls.assign_prefix(categories, original_title, infobox_name)

		extraction["latitude"], extraction["longitude"] = cls.assign_coordinates(infobox_data)
		
		if extraction["prefix"] in ("geo:waterfall", "geo:island", "geo:relief"):
			extraction["continent"] = cls.assign_continent(infobox_data)
		
		if extraction["prefix"] == "geo:waterfall":
			extraction["total_height"] = cls.assign_total_height(infobox_data)
		
		if extraction["prefix"] in ("geo:island", "geo:continent"):
			extraction["area"] = cls.assign_area(infobox_data)
			extraction["population"] = cls.assign_population(infobox_data)

		return extraction
	
	@staticmethod
	def assign_prefix(categories, original_title, infobox_name):
		
		if (re.search(r"poloostrovy\s+(?:na|ve?)", "\n".join(categories), re.I)
				or re.search(r"poloostrov", original_title, re.I)):
			return "geo:peninsula"
		elif (infobox_name in ["reliéf", "hora", "průsmyk", "pohoří", "sedlo"] 
				or re.search(r"reliéf|hora|průsmyk|pohoří|sedlo", original_title, re.I)):
			return "geo:relief"
		elif (infobox_name == "kontinent"
				or re.search(r"kontinent", original_title, re.I)):
			return "geo:continent"
		elif (infobox_name == "ostrov"
				or re.search(r"ostrov", original_title, re.I)):
			return "geo:island"
		elif (infobox_name == "vodopád"
				or re.search(r"vodopád", original_title, re.I)):
			return "geo:waterfall"
		else:
			return "geo:unknown"

	@staticmethod
	def assign_coordinates(infobox_data):
		latitude = ""
		longitude = ""

		# zeměpisná šířka
		keys = ["zeměpisná šířka", "zeměpisná_šířka"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				latitude = CoreUtils.get_latitude(CoreUtils.del_redundant_text(value))
				break

		# zeměpisná výška
		keys = ["zeměpisná výška", "zeměpisná_výška"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				longitude = CoreUtils.get_longitude(CoreUtils.del_redundant_text(value))
				break

		return (latitude, longitude)

	def assign_continent(cls, infobox_data):
		continent = ""
		# světadíl
		key = "světadíl"
		if key in infobox_data and infobox_data[key]:
			value = infobox_data[key]
			continent = cls.get_continent(CoreUtils.del_redundant_text(value))
		return continent

	@classmethod
	def assign_area(cls, infobox_data):
		area = ""
		# rozloha
		key = "rozloha"
		if key in infobox_data and infobox_data[key]:
			value = infobox_data[key]
			area = cls.get_area(CoreUtils.del_redundant_text(value))
		
		return area

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
	def assign_total_height(cls, infobox_data):
		height = ""
		keys = ["celková výška", "celková_výška"]
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				height = cls.get_total_height(CoreUtils.del_redundant_text(value))
				break
		return height

	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	##
	# @brief Převádí rozlohu geografické entity do jednotného formátu.
	# @param area - rozloha geografické entity v kilometrech čtverečních (str)
	@staticmethod
	def get_area(area):		
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

		return area

	##
	# Převádí světadíl, na kterém se geografická entita nachází, do jednotného formátu.
	# continent - světadíl, na kterém se geografická entita nachází (str)
	@staticmethod
	def get_continent(continent):
		continent = re.sub(r"\(.*?\)", "", continent)
		continent = re.sub(r"\[.*?\]", "", continent)
		continent = re.sub(r"<.*?>", "", continent)
		continent = re.sub(r"{{.*?}}", "", continent)
		continent = re.sub(r"\s+", " ", continent).strip()
		continent = re.sub(r", ?", "|", continent).replace("/", "|")

		return continent

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

	##
	# @brief Převádí celkovou výšku vodopádu do jednotného formátu.
	# @param height - ceková výška vodopádu (str)
	@staticmethod
	def get_total_height(height):
		height = re.sub(r"\(.*?\)", "", height)
		height = re.sub(r"\[.*?\]", "", height)
		height = re.sub(r"<.*?>", "", height)
		height = re.sub(r"{{.*?}}", "", height).replace("{", "").replace("}", "")
		height = re.sub(r"(?<=\d)\s(?=\d)", "", height).strip()
		height = re.sub(r"(?<=\d)\.(?=\d)", ",", height)
		height = re.sub(r"^\D*(?=\d)", "", height)
		height = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", height)
		height = "" if not re.search(r"\d", height) else height

		return height
