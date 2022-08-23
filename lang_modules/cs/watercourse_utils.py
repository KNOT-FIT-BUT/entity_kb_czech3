
import re
from core_utils import CoreUtils

class WatercourseUtils:

	@classmethod
	def extract_infobox(cls, ent_data, debugger):
		extraction = {
			"latitude": "",
			"longitude": "",
			"continents": "",
			"area": "",
			"length": "",
			"streamflow": "",
			"source_loc": ""
		}

		infobox_data = ent_data["infobox_data"]

		extraction["latitude"], extraction["longitude"] = cls.assign_coordinates(infobox_data)
		extraction["continents"] = cls.assign_continent(infobox_data)
		extraction["area"] = cls.assign_area(infobox_data)
		extraction["length"] = cls.assign_length(infobox_data)
		extraction["streamflow"] = cls.assign_streamflow(infobox_data)
		extraction["source_loc"] = cls.assign_source(infobox_data)

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
	def assign_area(cls, infobox_data):
		area = ""

		# plocha
		key = "plocha"
		if key in infobox_data and infobox_data[key]:
			value = infobox_data[key]
			area = cls.get_area(CoreUtils.del_redundant_text(value))

		return area

	@classmethod
	def assign_length(cls, infobox_data):
		length = ""
		
		# délka toku
		key = "délka"
		if key in infobox_data and infobox_data[key]:
			value = infobox_data[key]
			length = cls.get_length(CoreUtils.del_redundant_text(value))

		return length

	@classmethod
	def assign_source(cls, infobox_data):
		source = ""

		# pramen
		key = "pramen"
		if key in infobox_data and infobox_data[key]:
			value = infobox_data[key]
			source = cls.get_source_loc(CoreUtils.del_redundant_text(value))

		return source

	@classmethod
	def assign_streamflow(cls, infobox_data):
		streamflow = ""
		# průtok
		key = "průtok"
		if key in infobox_data and infobox_data[key]:
			value = infobox_data[key]
			streamflow = cls.get_streamflow(CoreUtils.del_redundant_text(value))
		return streamflow

	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	##
	# @brief Převádí plochu vodního toku do jednotného formátu.
	# @param area - plocha vodního toku v kilometrech čtverečních (str)
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
	# @brief Převádí světadíl, kterým vodní tok protéká, do jednotného formátu.
	# @param continent - světadíl, kterým vodní tok protéká (str)
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
	# @brief Převádí délku vodního toku do jenotného formátu.
	# @param length - délka vodního toku v kilometrech (str)
	@staticmethod
	def get_length(length):
		length = re.sub(r"\(.*?\)", "", length)
		length = re.sub(r"\[.*?\]", "", length)
		length = re.sub(r"<.*?>", "", length)
		length = re.sub(r"{{.*?}}", "", length).replace("{", "").replace("}", "")
		length = re.sub(r"(?<=\d)\s(?=\d)", "", length).strip()
		length = re.sub(r"(?<=\d)\.(?=\d)", ",", length)
		length = re.sub(r"^\D*(?=\d)", "", length)
		length = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", length)
		length = "" if not re.search(r"\d", length) else length

		return length

	##
	# @brief Převádí umístění pramene vodního toku do jednotného formátu.
	# @param source_loc - místo, kde vodní tok pramení (str)
	@staticmethod
	def get_source_loc(source_loc):
		source_loc = re.sub(r"\[.*?\]", "", source_loc)
		source_loc = re.sub(r"<.*?>", "", source_loc)
		source_loc = (
			re.sub(r"{{.*?}}", "", source_loc).replace("()", "").strip().strip(",")
		)
		source_loc = re.sub(r"\s+", " ", source_loc).strip()

		return source_loc

	##
	# @brief Převádí průtok vodního toku do jednotného formátu.
	# @param streamflow - průtok vodního toku v metrech krychlových za sekundu (str)
	@staticmethod
	def get_streamflow(streamflow):
		streamflow = re.sub(r"\(.*?\)", "", streamflow)
		streamflow = re.sub(r"\[.*?\]", "", streamflow)
		streamflow = re.sub(r"<.*?>", "", streamflow)
		streamflow = (
			re.sub(r"{{.*?}}", "", streamflow).replace("{", "").replace("}", "")
		)
		streamflow = re.sub(r"(?<=\d)\s(?=\d)", "", streamflow).strip()
		streamflow = re.sub(r"(?<=\d)\.(?=\d)", ",", streamflow)
		streamflow = re.sub(r"^\D*(?=\d)", "", streamflow)
		streamflow = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", streamflow)
		streamflow = "" if not re.search(r"\d", streamflow) else streamflow

		return streamflow

