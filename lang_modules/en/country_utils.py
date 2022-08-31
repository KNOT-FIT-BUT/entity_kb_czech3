
import re

from lang_modules.en.core_utils import CoreUtils

class CountryUtils:

	@staticmethod
	def extract_infobox(ent_data, debugger):
		
		extraction = {
			"prefix": "",
			"latitude": "",
			"longitude": "",
			"area": "",
			"population": ""
		}

		infobox_data, categories, title = (
			ent_data["infobox_data"],
			ent_data["categories"],
			ent_data["title"]
		)

		extraction["prefix"] = CountryUtils.assign_prefix(categories)
		
		extraction["latitude"], extraction["longitude"] = CoreUtils.assign_coordinates(infobox_data, debugger)
		extraction["area"] = CoreUtils.assign_area(infobox_data, debugger)
		extraction["population"] = CountryUtils.assign_population(infobox_data)

		return extraction

	@staticmethod
	def assign_prefix(categories):
		for category in categories:
			# TODO: "developed" is too specific
			if "developed" in category:
				continue
			if re.search(r"former.*?countries", category.lower(), re.I):
				return "country:former"
		return "country"

	##
    # @brief extracts and assigns population from infobox
	@staticmethod
	def assign_population(infobox_data):
		names = ("population_estimate", "population_census")
		for name in names:
			if name in infobox_data and infobox_data[name] != "":
				#print(f"{self.title}: estimate {self.infobox_data['population_estimate']}")				
				match = re.findall(r"[0-9,]+", infobox_data[name])
				if match:
					population = match[0].replace(',','')
					return population
		
		# if self.prefix != "country:former":
		# 	print(f"\n{self.title}: population not found ({self.link})")
		return ""

	##
	# @brief
	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords

		return extracted