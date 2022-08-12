##
# @file ent_event.py
# @brief contains EntEvent class - entity used for events
#
# @section ent_information entity information
# - start date
# - end date
# - locations
# - type
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

from ent_core import EntCore

from lang_modules.en.event_utils import EventUtils as EnUtils

utils = {
	"en": EnUtils
}

##
# @class EntEvent
# @brief entity used for events
class EntEvent(EntCore):
	##
    # @brief initializes the event entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntEvent, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.start_date = ""
		self.end_date = ""
		self.locations = []
		self.type = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.start_date,
			self.end_date,
			'|'.join(self.locations),
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

		self.start_date	= extraction["start_date"]
		self.end_date	= extraction["end_date"]
		self.locations	= extraction["locations"]
		self.type 		= extraction["type"]
	

