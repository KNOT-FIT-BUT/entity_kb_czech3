
import re
from lang_modules.cs.core_utils import CoreUtils

class WatercourseUtils:

	KEYWORDS = {
		"source": ["pramen"],
		"streamflow": ["průtok"],
		"length": ["délka"]
	}

	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	# ##
	# # @brief Převádí plochu vodního toku do jednotného formátu.
	# # @param area - plocha vodního toku v kilometrech čtverečních (str)
	# @staticmethod
	# def get_area(area):		
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
	# # @brief Převádí délku vodního toku do jenotného formátu.
	# # @param length - délka vodního toku v kilometrech (str)
	# @staticmethod
	# def get_length(length):
	# 	length = re.sub(r"\(.*?\)", "", length)
	# 	length = re.sub(r"\[.*?\]", "", length)
	# 	length = re.sub(r"<.*?>", "", length)
	# 	length = re.sub(r"{{.*?}}", "", length).replace("{", "").replace("}", "")
	# 	length = re.sub(r"(?<=\d)\s(?=\d)", "", length).strip()
	# 	length = re.sub(r"(?<=\d)\.(?=\d)", ",", length)
	# 	length = re.sub(r"^\D*(?=\d)", "", length)
	# 	length = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", length)
	# 	length = "" if not re.search(r"\d", length) else length
	# 	return length

	# ##
	# # @brief Převádí umístění pramene vodního toku do jednotného formátu.
	# # @param source_loc - místo, kde vodní tok pramení (str)
	# @staticmethod
	# def get_source_loc(source_loc):
	# 	source_loc = re.sub(r"\[.*?\]", "", source_loc)
	# 	source_loc = re.sub(r"<.*?>", "", source_loc)
	# 	source_loc = (
	# 		re.sub(r"{{.*?}}", "", source_loc).replace("()", "").strip().strip(",")
	# 	)
	# 	source_loc = re.sub(r"\s+", " ", source_loc).strip()
	# 	return source_loc

	# ##
	# # @brief Převádí průtok vodního toku do jednotného formátu.
	# # @param streamflow - průtok vodního toku v metrech krychlových za sekundu (str)
	# @staticmethod
	# def get_streamflow(streamflow):
	# 	streamflow = re.sub(r"\(.*?\)", "", streamflow)
	# 	streamflow = re.sub(r"\[.*?\]", "", streamflow)
	# 	streamflow = re.sub(r"<.*?>", "", streamflow)
	# 	streamflow = (
	# 		re.sub(r"{{.*?}}", "", streamflow).replace("{", "").replace("}", "")
	# 	)
	# 	streamflow = re.sub(r"(?<=\d)\s(?=\d)", "", streamflow).strip()
	# 	# streamflow = re.sub(r"(?<=\d)\.(?=\d)", ",", streamflow)
	# 	streamflow = re.sub(r"^\D*(?=\d)", "", streamflow)
	# 	streamflow = re.sub(r"^(\d+(?:,\d+)?)[^\d,]+.*$", r"\1", streamflow)
	# 	streamflow = "" if not re.search(r"\d", streamflow) else streamflow
	# 	return streamflow

