##
# @file ent_country.py
# @brief contains EntCountry class - entity used for countries
#
# @section ent_information entity information
# - area
# - population
# - latitude
# - longtitude
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from ent_core import EntCore

from lang_modules.en.country_utils import CountryUtils as EnUtils
from lang_modules.cs.country_utils import CountryUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}

##
# @class EntCountry
# @brief entity used for countries
class EntCountry(EntCore):
	##
    # @brief initializes the country entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntCountry, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.area = ""
		self.population = ""
		self.latitude = ""
		self.longitude = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.latitude,
			self.longitude,
			self.area,
			self.population
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions) and assigns prefix
	def assign_values(self, lang):
		lang_utils = utils[lang]

		# extraction = lang_utils.extract_text(extraction, ent_data, self.d)

		self.prefix = lang_utils.assign_prefix(self.categories)
		self.latitude, self.longitude = self.core_utils.assign_coordinates(self)
		self.area = self.assign_area()
		self.assign_population()


	##
    # @brief extracts and assigns population from infobox
	#
	# TODO: coef?
	def assign_population(self):
		data = self.get_infobox_data(utils[self.lang].KEYWORDS["population"], return_first=True)
		if data:
			data = re.sub(r"&nbsp;", "", data)
			data = re.sub(r"(?<=\d)\s(?=\d)", "", data)
			data = data.replace(',','')
			match = re.findall(r"\d+", data)
			if match:
				data = match[0]				
				self.population = data

