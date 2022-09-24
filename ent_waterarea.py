##
# @file ent_waterarea.py
# @brief contains EntWaterArea class - entity used for lakes, seas and oceans
#
# @section ent_information entity information
# - continents
# - latitude
# - longtitude
# - area
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from ent_core import EntCore

from lang_modules.en.waterarea_utils import WaterareaUtils as EnUtils
from lang_modules.cs.waterarea_utils import WaterareaUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}

##
# @class EntWaterArea
# @brief entity used for lakes, seas and oceans
class EntWaterArea(EntCore):
	##
    # @brief initializes the waterarea entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntWaterArea, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.area = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.continents,
			self.latitude,
			self.longitude,
			self.area
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self, lang):
		lang_utils = utils[lang]
		self.latitude, self.longitude = self.core_utils.assign_coordinates(self)
		self.area = self.assign_area()		
		self.continents = lang_utils.assign_continents(self)

