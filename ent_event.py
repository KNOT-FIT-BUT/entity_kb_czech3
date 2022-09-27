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

import re

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
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, keywords):
		super(EntEvent, self).__init__(title, prefix, link, data, langmap, redirects, sentence, keywords)

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
		self.start_date, self.end_date = lang_utils.assign_dates(self.infobox_data)
		self.assign_locations()
		self.assign_type()

		name = ""
		if self.infobox_name and self.infobox_name != "event":
			name = self.infobox_name.lower()

		if not self.type:			
			self.type = name
		
		if name == "election" and self.type:
			self.type = f"{self.type} election"
		else:
			self.type = "election"

		self.extract_non_person_aliases()
	
	##
    # @brief extracts and assigns locations from infobox
	def assign_locations(self):
		locations = []
		
		keys = [
			"place", 
			"country",
			"location",
			"areas",
			"city",
			"host_city",
			"cities",
			"affected",
			"site",
			"venue"
		]
		data = self.get_infobox_data(keys, return_first=True)
		if data:
			data = self.remove_templates(data)
			
			if re.search(r"[a-z][A-Z]", data):
				string = re.sub(r"([a-z])([A-Z])", r"\1|\2", data)
				split = string.split("|")
				found = False
				for s in split:
					if "," not in s:
						found = True
						break
				if found:
					string = re.sub(r"([a-z])([A-Z])", r"\1, \2", data)
					locations.append(string)
				else:
					locations = split
				self.locations = "|".join(locations)
				return
			
			if "," in data:
				split = data.split(",") 
				if len(split) > 5:
					locations = [item.strip() for item in split]
					self.locations = "|".join(locations)
					return

			locations.append(data)
			self.locations = "|".join(locations)

	##
    # @brief extracts and assigns type from infobox
	def assign_type(self):
		data = self.get_infobox_data(["type"], return_first=True)
		if data:
			self.type = self.remove_templates(data).lower()

