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

from ent_core import EntCore

from lang_modules.en.geo_utils import GeoUtils as EnUtils

utils = {
	"en": EnUtils
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

		ent_data = {
			"infobox_data": self.infobox_data,
			"infobox_name": self.infobox_name,
			"coords": self.coords,
			"title": self.title
		}

		extraction = lang_utils.extract_infobox(ent_data, self.d)
		extraction = lang_utils.extract_text(extraction, ent_data, self.d)

		self.prefix 		= extraction["prefix"]

		self.continent 		= extraction["continent"]
		self.latitude 		= extraction["latitude"]
		self.longitude 		= extraction["longitude"]
		self.area 			= extraction["area"]
		self.population		= extraction["population"]
		self.total_height	= extraction["total_height"]
