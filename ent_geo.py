##
# @file ent_geo.py
# @brief contains EntGeo class - entity used for mountains, islands, waterfalls, peninsulas and continents
#
# @section ent_information entity information
# general:
# - latitude
# - longtitude
#
# waterfalls:
# - continent
# - total height
#
# islands:
# - continent
# - area
# - population
#
# continents:
# - area
# - population
# 
# reliefs: 
# - continent
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from debugger import Debugger as debug

from ent_core import EntCore
from lang_modules.en.geo_utils import GeoUtils as EnUtils
from lang_modules.cs.geo_utils import GeoUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}

##
# @class EntGeo
# @brief entity used for mountains, islands, waterfalls, peninsulas and continents
class EntGeo(EntCore):
	##
    # @brief initializes the geo entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntGeo, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.continent = ""
		self.latitude = ""
		self.longitude = ""
		self.area = ""
		self.population = ""
		self.total_height = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):

		data = []

		if self.prefix in ("geo:waterfall", "geo:island", "geo:relief"):
			data += [self.continent]

		data += [self.latitude, self.longitude]

		if self.prefix in ("geo:island", "geo:continent"):
			data += [self.area, self.population]

		if self.prefix == "geo:waterfall":
			data += [self.total_height]

		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions) and assigns prefix
	def assign_values(self, lang):
		lang_utils = utils[lang]
		self.prefix = lang_utils.assign_prefix(self)
		self.latitude, self.longitude = self.core_utils.assign_coordinates(self)

		if self.prefix == "geo:waterfall":
			self.assign_height()

		if self.prefix in ("geo:island", "geo:continent"):
			self.area = self.assign_area()
			self.population = self.assign_population()

		if self.prefix in ("geo:island", "geo:relief", "geo:waterfall"):
			self.assign_continent()

		self.extract_non_person_aliases()

	##
    # @brief extracts and assigns height from infobox
	def assign_height(self):
		def fix_height(height):
			height = re.sub(r"\(.*?\)", "", height)
			height = re.sub(r"&nbsp;", " ", height)
			height = re.sub(r"(?<=\d)\s(?=\d)", "", height)
			height = re.sub(r",(?=\d{3})", "", height)
			height = height.replace(",", ".")
			match = re.search(r"\{\{(?:convert|cvt)\|([\d\.]+)\|([^\|]+)(?:\|.*?)?\}\}", height, flags=re.I)
			if match:
				number = match.group(1).strip()
				unit = match.group(2).strip()
				height = self.convert_units(number, unit)
			height = re.sub(r"\{\{.*?\}\}", "", height)
			match = re.search(r"^([\d\.]+)(?:\s?([^\s]+))?", height)
			if match:
				number = match.group(1).strip()
				unit = match.group(2)
				if unit:
					unit = unit.strip(".").strip()
					height = self.convert_units(number, unit)
				else:
					height = number
			else:
				height = ""
			return height
		
		data = self.get_infobox_data(utils[self.lang].KEYWORDS["height"], return_first=True)
		if data:
			data = fix_height(data)
			self.total_height = data

	##
	# @brief description
	#
	# NOT UNIFIED - en version is not currently extracting continents in watercourse entities
	def assign_continent(self):
		data = self.get_infobox_data(["světadíl"], return_first=True)
		if data:
			data = self.get_continent(self.core_utils.del_redundant_text(data))
			self.continent = data

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
