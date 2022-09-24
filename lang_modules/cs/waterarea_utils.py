
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
