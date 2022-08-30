
import re

from lang_modules.en.core_utils import CoreUtils

class SettlementUtils:

	def extract_infobox(ent_data, debugger):
		
		extraction = {
			"country": "",
			"latitude": "",
			"longitude": "",
			"area": "",
			"population": ""
		}

		infobox_data = ent_data["infobox_data"]

		extraction["country"] = SettlementUtils.assign_country(infobox_data)
		extraction["latitude"], extraction["longitude"] = CoreUtils.assign_coordinates(infobox_data, debugger)
		extraction["area"] = SettlementUtils.assign_area(infobox_data)
		extraction["population"] = SettlementUtils.assign_population(infobox_data)

		return extraction

	##
    # @brief extracts and assigns area from infobox
	# @todo update this - look at country area extraction
	@staticmethod
	def assign_area(infobox_data):
		
		area = ""

		if "area_total_km2" in infobox_data:
			area = infobox_data['area_total_km2']
			area = area.replace(",", "")
			area = re.sub(r"\{\{.+\}\}", "", area)
			
		# else:
		# 	print(f"{self.title}: area not found")

		return area

	##
    # @brief extracts and assigns population from infobox
	@staticmethod
	def assign_population(infobox_data):
		
		population = ""

		# population_total
		if "population_total" in infobox_data:
			if infobox_data["population_total"] != "":
				match = re.findall(r"[0-9,]+", infobox_data["population_total"])
				if match:
					population = match[0].replace(',','')
					
		# else: 
		# 	print(f"{self.title}: population not found")

		return population

	##
    # @brief extracts and assigns country from infobox
	@staticmethod
	def assign_country(infobox_data):
		
		country = ""
		
		# subdivision_name
		if "subdivision_name" in infobox_data:
			if infobox_data["subdivision_name"] != "":
				country = infobox_data["subdivision_name"]  
				country = re.sub(r"\[|\]|\{|\}", "", country, flags=re.DOTALL)
				split = country.split("|")
				if len(split) > 1:
					country = split[-1]

		# else: 
		# 	print(f"{self.title}: country not found")	
		
		return country

	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords

		return extracted