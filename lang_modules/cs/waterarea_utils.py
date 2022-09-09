
import re
from lang_modules.cs.core_utils import CoreUtils

class WaterareaUtils:
		
	@classmethod
	def assign_continents(cls, waterarea):
		continent = ""

		# světadíl
		key = "světadíl"
		if key in waterarea.infobox_data and waterarea.infobox_data[key]:
			value = waterarea.infobox_data[key]
			continent = cls.get_continent(CoreUtils.del_redundant_text(value))

		return continent

	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		return extracted

	# ##
	# # @brief Převádí rozlohu vodní plochy do jednotného formátu.
	# # @param area - rozloha vodní plochy v kilometrech čtverečních (str)
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

