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

from entities.ent_core import EntCore

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
		return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")

	##
    # @brief tries to assign entity information (calls the appropriate functions) and assigns prefix
	def assign_values(self):

		for category in self.categories:
			# TODO: "developed" is too specific
			if "developed" in category:
				continue
			if re.search(r"former.*?countries", category.lower(), re.I):
				self.prefix += ":former"
				break

		self.assign_area()
		self.assign_population()
		self.assign_coordinates()

	##
    # @brief extracts and assigns latitude and longtitude from infobox
	def assign_coordinates(self):
		if "coordinates" in self.infobox_data and self.infobox_data["coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["coordinates"])
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
		names = ("area_km2", "area_total_km2")
		for name in names:
			if name in self.infobox_data and self.infobox_data[name] != "":
				area = self.infobox_data[name]
				area = area.replace(",", "")
				area = re.sub(r"\{\{.+\}\}", "", area)
				self.area = area
				return

		names = ("area_sq_mi", "area_total_sq_mi")
		for name in names:
			if name in self.infobox_data and self.infobox_data[name] != "":
				area = self.infobox_data[name]
				area = area.replace(",", "")
				area = re.sub(r"\{\{.+\}\}", "", area)
				self.area = self.convert_units(area, "sqmi")
				return

		if self.prefix != "country:former":
			#print(f"\n{self.link}")
			pass

	##
    # @brief extracts and assigns population from infobox
	def assign_population(self):
		names = ("population_estimate", "population_census")
		for name in names:
			if name in self.infobox_data and self.infobox_data[name] != "":
				#print(f"{self.title}: estimate {self.infobox_data['population_estimate']}")				
				match = re.findall(r"[0-9,]+", self.infobox_data[name])
				if match:
					self.population = match[0].replace(',','')
					return
		
		# if self.prefix != "country:former":
		# 	print(f"\n{self.title}: population not found ({self.link})")
		pass
