##
# @file ent_settlement.py
# @brief contains EntSettlement class - entity used for settlements
#
# @section ent_information entity information
# - area
# - population
# - latitude
# - longtitude
# - country
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from entities.ent_core import EntCore

##
# @class EntSettlement
# @brief entity used for settlements
class EntSettlement(EntCore):
	##
    # @brief initializes the settlement entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntSettlement, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.area = ""
		self.population = ""
		self.latitude = ""
		self.longitude = ""
		self.country = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		return self.serialize(f"{self.country}\t{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self):
		self.assign_area()
		self.assign_population()
		self.assign_coordinates()
		self.assign_country()

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
		if "area_total_km2" in self.infobox_data:
			area = self.infobox_data['area_total_km2']
			area = area.replace(",", "")
			area = re.sub(r"\{\{.+\}\}", "", area)
			self.area = area
		# else:
		# 	print(f"{self.title}: area not found")
		pass

	##
    # @brief extracts and assigns population from infobox
	def assign_population(self):
		# population_total
		if "population_total" in self.infobox_data:
			if self.infobox_data["population_total"] != "":
				match = re.findall(r"[0-9,]+", self.infobox_data["population_total"])
				if match:
					self.population = match[0].replace(',','')
					return
		# else: 
		# 	print(f"{self.title}: population not found")
		pass

	##
    # @brief extracts and assigns country from infobox
	def assign_country(self):
		# subdivision_name
		if "subdivision_name" in self.infobox_data:
			if self.infobox_data["subdivision_name"] != "":
				country = self.infobox_data["subdivision_name"]  
				country = re.sub(r"\[|\]|\{|\}", "", country, flags=re.DOTALL)
				split = country.split("|")
				if len(split) > 1:
					country = split[-1]
				self.country = country
		# else: 
		# 	print(f"{self.title}: country not found")	
		pass
