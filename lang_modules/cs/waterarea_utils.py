
import re
from core_utils import CoreUtils

class WaterareaUtils:

	@classmethod
	def extract_infobox(cls, ent_data, debugger):
		extraction = {
			"latitude": "",
			"longitude": "",
			"area": "",
			"continents": ""
		}

		infobox_data = ent_data["infobox_data"]

		extraction["latitude"], extraction["longitude"] = cls.assign_coordinates(infobox_data)
		extraction["continents"] = cls.assign_continent(infobox_data)
		extraction["area"] = cls.assign_area(infobox_data)

		return extraction
		
	@classmethod
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

	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	##
	# @brief Převádí rozlohu vodní plochy do jednotného formátu.
	# @param area - rozloha vodní plochy v kilometrech čtverečních (str)
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
	# @brief Převádí světadíl, na kterém se vodní plocha nachází, do jednotného formátu.
	# @param continent - světadíl, na kterém se vodní plocha nachází (str)
	@staticmethod
	def get_continent(continent):
		continent = re.sub(r"\(.*?\)", "", continent)
		continent = re.sub(r"\[.*?\]", "", continent)
		continent = re.sub(r"<.*?>", "", continent)
		continent = re.sub(r"{{.*?}}", "", continent)
		continent = re.sub(r"\s+", " ", continent).strip()
		continent = re.sub(r", ?", "|", continent).replace("/", "|")

		return continent

