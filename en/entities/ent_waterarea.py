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

from entities.ent_core import EntCore

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
		return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.continents}")

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self):
		self.assign_area()
		self.assign_coordinates()
		self.assign_continents()

	##
    # @brief extracts and assigns latitude and longtitude from infobox
	def assign_coordinates(self):
		possible_keys = ["coordinates", "coords"]
		for key in possible_keys: 
			if key in self.infobox_data and self.infobox_data[key] != "":
				coords = self.get_coordinates(self.infobox_data[key])
				if all(coords):
					self.latitude, self.longitude = coords
				return
		
		if self.coords != "":
			coords = self.get_coordinates(self.coords)
			if all(coords):
				self.latitude, self.longitude = coords

	##
    # @brief extracts and assigns area from infobox
	def assign_area(self):
		"""
        pokusí se extrahovat rozlohu z infoboxu area
        """
		if "area" in self.infobox_data:
			area = self.infobox_data['area']
			if area != "":
				match = re.search(r"{{.*?\|([0-9\.]+)\|(\w+).*?}}", area)
				if match:
					self.area = self.convert_units(match.group(1), match.group(2))
				else:
					#print(f"{self.title}: did not match area ({area})")
					pass
		else:
			#print(f"{self.title}: area not found")
			pass

	##
    # @brief extracts and assigns continents from infobox
	def assign_continents(self):
		"""
        pokusí se extrahovat kontinenty z infoboxu location
        """
		if "location" in self.infobox_data:
			location = self.infobox_data['location']
			if location != "":
				continents = ["Asia", "Africa", "Europe", "North America", "South America", "Australia", "Oceania", "Antarctica"]
				patterns = [r"Asia", r"Africa", r"Europe", r"North[^,]+America", r"South[^,]+America", r"Australia", r"Oceania", r"Antarctica"]
				curr_continents = []
				for i in range(len(continents)):
					match = re.search(patterns[i], location)
					if match:					
						curr_continents.append(continents[i])
				self.continents  = "|".join(curr_continents)
				return

		#print(f"{self.title}: did not find location")
		pass
