##
# @file waterarea_utils.py
# @brief en specific waterarea utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re

class WaterareaUtils:

	##
    # @brief extracts and assigns continents from infobox
	@staticmethod
	def assign_continents(waterarea):
		continents = ""

		if "location" in waterarea.infobox_data:
			location = waterarea.infobox_data['location']
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
