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

from entities.ent_core import EntCore

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
		return self.serialize(f"{self.start_date}\t{self.end_date}\t{'|'.join(self.locations)}\t{self.type}")

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self):		
		self.assign_dates()
		self.assign_locations()
		self.assign_type()

	##
    # @brief extracts and assigns start date and end date variables from infobox
	def assign_dates(self):
		keys = ["year", "start_date", "first_aired", "election_date"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.extract_date(data)
				self.start_date = data[0]

		keys = ["end_date"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.extract_date(data)
				self.end_date = data[0]

		keys = ["date"]
		
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				split = data.split("–")
				split = [item.strip() for item in split if item != ""]
				if len(split) == 1:
					date = self.extract_date(split[0])
					self.start_date = date[0]
					self.end_date = date[1]						
					break
				else:
					
					# 19-25 September 2017 -> 19 September 2017 - 25 September 2017
					if re.search(r"^[0-9]+$", split[0]):
						match = re.search(r"^[0-9]+?\s+?([a-z]+?\s+?[0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return

					# January-September 2017 -> January 2017 - September 2017
					if re.search(r"^[a-z]+$", split[0], re.I):
						match = re.search(r"^[a-z]+?\s+?([0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return

					self.start_date = self.extract_date(split[0])[0]
					self.end_date = self.extract_date(split[1])[0]

	##
    # @brief extracts and assigns locations from infobox
	def assign_locations(self):		
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

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
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
						self.locations.append(string)
					else:
						self.locations = split
					break
				
				if "," in data:
					split = data.split(",") 
					if len(split) > 5:
						self.locations = [item.strip() for item in split]
						break

				self.locations.append(data)
				break

	##
    # @brief extracts and assigns type from infobox
	def assign_type(self):
		
		type = ""
		name = ""

		if "type" in self.infobox_data and self.infobox_data["type"] != "":
			type = self.infobox_data["type"]
			type = self.remove_templates(type).lower()

		if self.infobox_name != "" and self.infobox_name != "event":
			name = self.infobox_name.lower()

		if name == "election" and type != "":
			self.type = f"{type} election"
			return
		else:
			self.type = "election"

		if type != "":
			self.type = type
		else:
			self.type = name

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

