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

import re

from entities.ent_core import EntCore

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
		"""
        serializuje parametry třídy EntGeo
        """
		if self.prefix == "geo:waterfall":
			return self.serialize(f"{self.continent}\t{self.latitude}\t{self.longitude}\t{self.total_height}")
		elif self.prefix == "geo:island":
			return self.serialize(f"{self.continent}\t{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")
		elif self.prefix == "geo:continent":
			return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")
		elif self.prefix == "geo:relief":
			return self.serialize(f"{self.continent}\t{self.latitude}\t{self.longitude}")

		return self.serialize(f"{self.latitude}\t{self.longitude}")

	##
    # @brief tries to assign entity information (calls the appropriate functions) and assigns prefix
	def assign_values(self):
		self.prefix += f":{self.get_prefix(self.infobox_name)}"

		if self.prefix == "geo:":
			self.d.log_message(self.link)

		self.assign_coordinates()
		if self.prefix == "geo:waterfall":
			# assign continent
			self.assign_height()
		elif self.prefix in ["geo:island", "geo:continent"]:
			self.assign_area()
			self.assign_population()

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
				return

	##
    # @brief extracts and assigns height from infobox
	def assign_height(self):
		if "height" in self.infobox_data and self.infobox_data["height"] != "":
			height = self.infobox_data["height"]

			# match "{{convert }}" format
			match = re.search(r"{{(?:convert|cvt)\|([0-9]+)\|(\w+).*}}", height)
			if match:
				self.total_height = self.convert_units(match.group(1), match.group(2))
			else:
				height = re.sub(r"\(.*\)", "", height).strip()
				split = height.split(" ")
				if len(split) > 1:
					self.total_height = self.convert_units(split[0], split[1])
				else:
					match = re.search(r"([0-9]+)(\w+)", split[0])
					if match:
						self.total_height = self.convert_units(match.group(1), match.group(2))			
	
	##
    # @brief extracts and assigns area from infobox
	def assign_area(self):
		area_infoboxes = ["area_km2", "area"]
		for a in area_infoboxes:
			if a in self.infobox_data and self.infobox_data[a]:
				area = self.infobox_data[a]
				area = re.sub(r",|\(.*\)", "", area).strip()
				
				# {{convert|[number]|[km2 / sqmi]}}
				match = re.search(r"{{.*?\|([0-9]+)\s?\|(\w+).*?}}", area)
				if match:
					self.area = self.convert_units(match.group(1), match.group(2))
					break
				
				# [number] [km2 / sqmi]
				split = area.split(" ")
				if len(split) > 1:
					self.area = self.convert_units(split[0], split[1])
				else:
					try:
						number = float(area)
						self.area = str(number if number % 1 != 0 else int(number))
					except:
						self.d.log_message(f"{self.title}: error while converting area to float - {area} ({self.link})")
						return
				break

	##
    # @brief extracts and assigns population from infobox
	def assign_population(self):
		if "population" in self.infobox_data and self.infobox_data["population"]:
			population = self.infobox_data["population"]
			population = re.sub(r",|\(.*\)", "", population).strip()
			
			if population.lower() == "uninhabited":
				self.population = 0
				return
			
			match = re.search(r"([0-9\.]+)\s+(\w+)", population)
			if match:
				#print(match.groups())
				if match.group(2) == "billion":
					self.population = round(float(match.group(1)) * 1e9)
				# add more if needed
				return

			match = re.search(r"([0-9\.]+)", population)
			if match:
				self.population = match.group(1)			

	##
    # @brief assigns prefix based on infobox name
    #
    # geo:waterfall, geo:island, geo:relief, geo:peninsula or geo:continent
	@staticmethod
	def get_prefix(name):
		prefix = ""
		
		pattern = r"(waterfall|islands?|mountain|peninsulas?|continent)"
		match = re.search(pattern, name, re.I)
		if match:
			prefix = match.group(1).lower()

		if prefix in ("island", "islands"):
			prefix = "island"
		if prefix == "mountain":
			prefix = "relief"
		if prefix == "peninsulas":
			prefix = "peninsula"

		return prefix
