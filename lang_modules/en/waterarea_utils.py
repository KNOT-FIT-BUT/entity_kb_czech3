
import re

from lang_modules.en.core_utils import CoreUtils

class WaterareaUtils:

	def extract_infobox(ent_data, debugger):
		
		extraction = {
			"latitude": "",
			"longitude": "",
			"area": "",
			"continents": ""
		}

		infobox_data = ent_data["infobox_data"]

		extraction["latitude"], extraction["longitude"] = CoreUtils.assign_coordinates(infobox_data, debugger)
		extraction["area"] = WaterareaUtils.assign_area(infobox_data, debugger)
		extraction["continents"] = WaterareaUtils.assign_continents(infobox_data)

		return extraction

	##
    # @brief extracts and assigns area from infobox
	@staticmethod
	def assign_area(infobox_data, debugger):

		area = ""

		if "area" in infobox_data:
			area_match = infobox_data['area']
			if area_match != "":
				match = re.search(r"{{.*?\|([0-9\.]+)\|(\w+).*?}}", area_match)
				if match:
					area = CoreUtils.convert_units(match.group(1), match.group(2), debugger)

		#print(f"{self.title}: did not match area ({area})")
		#print(f"{self.title}: area not found")

		return area

	##
    # @brief extracts and assigns continents from infobox
	@staticmethod
	def assign_continents(infobox_data):	
		continents = ""

		if "location" in infobox_data:
			location = infobox_data['location']
			if location != "":
				continents = ["Asia", "Africa", "Europe", "North America", "South America", "Australia", "Oceania", "Antarctica"]
				patterns = [r"Asia", r"Africa", r"Europe", r"North[^,]+America", r"South[^,]+America", r"Australia", r"Oceania", r"Antarctica"]
				curr_continents = []
				for i in range(len(continents)):
					match = re.search(patterns[i], location)
					if match:					
						curr_continents.append(continents[i])
				continents  = "|".join(curr_continents)				

		#print(f"{self.title}: did not find location")
		
		return continents

	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords
		
		return extracted
