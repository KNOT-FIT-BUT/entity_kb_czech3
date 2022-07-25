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

import re

from entities.ent_core import EntCore
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
		return self.serialize(f"{self.founded}\t{self.cancelled}\t{self.location}\t{self.type}")

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self):
		self.assign_dates()
		self.assign_location()
		self.assign_type()

	##
    # @brief extracts and assigns founded and cancelled variables from infobox
	def assign_dates(self):
		
		keys = ["formation", "foundation", "founded", "fouded_date", "established"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				date = self.extract_date(data)
				if len(date) >= 1:
					self.founded = date[0]
					break

		keys = ["defunct", "banned", "dissolved"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				date = self.extract_date(data)
				if len(date) >= 1:
					self.cancelled = date[0]
					break

		keys = ["active", "dates"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				splitter = '-'
				if '–' in data:
					splitter = '–'
				data = data.split(splitter)
				if len(data) == 2:
					date = self.extract_date(data[0])
					if self.founded == "":
						self.founded = date[0]
					date = self.extract_date(data[1])
					if self.cancelled == "":
						self.cancelled = date[0]
					break

	##
    # @brief extracts and assigns location from infobox
	def assign_location(self):
		
		location = ""
		country = ""
		city = ""

		keys = ["location", "headquarters", "hq_location", "area"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.remove_templates(data)
				location = data
				break
		
		keys = ["location_country", "country", "hq_location_country"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.remove_templates(data)
				country = data
				break

		keys = ["location_city", "hq_location_city"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.remove_templates(data)
				city = data
				break

		if city != "" and country != "":
			self.location = f"{city}, {country}"
		else:
			if location != "":
				self.location = location
			elif country != "":
				self.location = country
			else:
				self.location = city

	##
    # @brief extracts and assigns type from infobox
	def assign_type(self):
		if "type" in self.infobox_data and self.infobox_data["type"] != "":
			data = self.infobox_data["type"]
			data = self.remove_templates(data)
			self.type = data
			return

		if self.infobox_name != "":
			if self.infobox_name.lower() != "organization":
				self.type = self.infobox_name

	##
	# @brief removes wikipedia formatting
	# @param data - string with wikipedia formatting
	# @return string without wikipedia formatting
	@staticmethod
	def remove_templates(data):
		data = re.sub(r"\{\{.*?\}\}", "", data)
		data = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", data)
		data = re.sub(r"\[|\]|'|\(\)", "", data)
		return data