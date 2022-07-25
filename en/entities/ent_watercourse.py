##
# @file ent_watercourse.py
# @brief contains EntWaterCourse class - entity used for rivers, creeks, streams, etc.
#
# @section ent_information entity information
# - continents
# - latitude
# - longtitude
# - length
# - area
# - streamflow
# - source_loc
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from entities.ent_core import EntCore

##
# @class EntWaterCourse
# @brief entity used for rivers, creeks, streams, etc.
class EntWaterCourse(EntCore):
	##
    # @brief initializes the watercourse entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntWaterCourse, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.length = ""
		self.area = ""
		self.streamflow = ""
		self.source_loc = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		return self.serialize(f"{self.continents}\t{self.latitude}\t{self.longitude}\t{self.length}\t{self.area}\t{self.streamflow}\t{self.source_loc}")

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self):
		#print(self.title)
		# self.assign_continents()
		self.assign_coordinates()
		self.assign_length()
		self.assign_area()
		self.assign_streamflow()
		self.assign_source_loc()	

	# def assign_continents(self):
	# 	# cant match from infobox
	# 	pass

	##
    # @brief extracts and assigns latitude and longtitude from infobox
	def assign_coordinates(self):
		if "source1_coordinates" in self.infobox_data and self.infobox_data["source1_coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["source1_coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords

	##
    # @brief extracts and assigns length from infobox
	def assign_length(self):
		# | length = {{convert|352|km|mi|abbr=on}}
		if "length" in self.infobox_data:
			length = self.infobox_data["length"]
			if length != "":
				match = re.search(r"{{(?:[Cc]onvert|cvt)\|([0-9.]+)\|(.+?)(?:\|.+?)?}}", length)
				if match:
					self.length = self.convert_units(match.group(1), match.group(2))
				return
		
		#print(f"{self.title}: did not find length")
		pass
		
	##
    # @brief extracts and assigns area from infobox
	def assign_area(self):
		# | basin_size        = {{convert|4506|km2|abbr=on}}
		if "basin_size" in self.infobox_data:
			area = self.infobox_data["basin_size"]
			if area != "":
				match = re.search(r"{{.*?\|([0-9.,]+)\|(\w+).*?}}", area)
				if match:
					number = re.sub(r",", "", match.group(1))
					self.area = self.convert_units(number, match.group(2))
					return
				else:
					self.d.log_message(f"{self.title}: did not match area ({area})")
		
		#print(f"\narea empty or not found ({self.link})")
		pass

	##
    # @brief extracts and assigns streamflow from infobox
	def assign_streamflow(self):
		# | discharge1_avg     = {{convert|593000|cuft/s|m3/s|abbr=on}}
		if "discharge1_avg" in self.infobox_data:
			streamflow = self.infobox_data["discharge1_avg"]
			if streamflow != "":
				streamflow = streamflow.replace(",", "")
				match = re.search(r"{{.*?\|([0-9.,]+)\|((?:\w|\/)+).*?}}", streamflow)
				if match:
					self.streamflow = self.convert_units(match.group(1), match.group(2))
				else:
					self.d.log_message(f"did not match streamflow ({streamflow}) [{self.link}]")
		
		#print(f"{self.title}: streamflow empty or not found")
		pass

	##
    # @brief extracts and assigns source location from infobox
	def assign_source_loc(self):
		# format: source1_location = near [[Hollenthon, Austria|Hollenthon]], [[Lower Austria]]
		if "source1_location" in self.infobox_data:
			source = self.infobox_data["source1_location"]
			if source != "":
				source = re.sub(r"\[\[([^\]]+?)\|([^\]]+?)\]\]", r"\2", source)
				source = re.sub(r"{{[^}]+?\|([^}]+?)(?:\|[^}]+?)?}}", r"\1", source)
				source = re.sub(r"\[|\]|\'", "", source)
				self.source_loc = source
				return
		
		#print(f"{self.title}: did not found source location")
		pass