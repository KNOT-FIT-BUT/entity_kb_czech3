##
# @file ent_organisation.py
# @brief contains EntOrganisation class - entity used for organisations
#
# @section ent_information entity information
# - founded
# - cancelled
# - location
# - type
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

from ent_core import EntCore

from lang_modules.en.organisation_utils import OrganisationUtils as EnUtils

utils = {
	"en": EnUtils
}

##
# @class EntOrganisation
# @brief entity used for organisations
class EntOrganisation(EntCore):
	##
    # @brief initializes the organisation entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntOrganisation, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.founded = ""
		self.cancelled = ""
		self.location = ""
		self.type = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.founded,
			self.cancelled,
			self.location,
			self.type
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self, lang):
		lang_utils = utils[lang]

		ent_data = {
			"infobox_data": self.infobox_data,
			"infobox_name": self.infobox_name
		}

		extraction = lang_utils.extract_infobox(ent_data, self.d)
		extraction = lang_utils.extract_text(extraction, ent_data, self.d)

		self.founded	= extraction["founded"]
		self.cancelled	= extraction["cancelled"]
		self.location	= extraction["location"]
		self.type 		= extraction["type"]

	