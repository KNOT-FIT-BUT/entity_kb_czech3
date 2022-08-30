
import re

from lang_modules.en.core_utils import CoreUtils

class GeoUtils:

	@staticmethod
	def extract_infobox(ent_data, debugger):

		extraction = {
			"prefix": "",
			"continent": "",
			"latitude": "",
			"longitude": "",
			"area": "",
			"population": "",
			"total_height": ""
		}

		infobox_data, infobox_name = (
			ent_data["infobox_data"],
			ent_data["infobox_name"]
		)

		extraction["prefix"] = GeoUtils.assign_prefix(infobox_name)

		extraction["latitude"], extraction["longitude"] = CoreUtils.assign_coordinates(infobox_data, debugger)
		if extraction["prefix"] == "geo:waterfall":
			extraction["total_height"] = GeoUtils.assign_height(infobox_data, debugger)
		elif extraction["prefix"] in ("geo:island", "geo:continent"):
			extraction["area"] = GeoUtils.assign_area(infobox_data, debugger)
			extraction["population"] = GeoUtils.assign_population(infobox_data)

		return extraction

	##
    # @brief extracts and assigns height from infobox
	@staticmethod
	def assign_height(infobox_data, debugger):
		total_height = ""
		
		if "height" in infobox_data and infobox_data["height"] != "":
			height = infobox_data["height"]

			# match "{{convert }}" format
			match = re.search(r"{{(?:convert|cvt)\|([0-9]+)\|(\w+).*}}", height)
			if match:
				total_height = CoreUtils.convert_units(match.group(1), match.group(2), debugger)
			else:
				height = re.sub(r"\(.*\)", "", height).strip()
				split = height.split(" ")
				if len(split) > 1:
					total_height = CoreUtils.convert_units(split[0], split[1], debugger)
				else:
					match = re.search(r"([0-9]+)(\w+)", split[0])
					if match:
						total_height = CoreUtils.convert_units(match.group(1), match.group(2), debugger)

		return total_height			
	
	##
    # @brief extracts and assigns area from infobox
	@staticmethod
	def assign_area(infobox_data, debugger):
		area = ""

		area_infoboxes = ["area_km2", "area"]
		for a in area_infoboxes:
			if a in infobox_data and infobox_data[a]:
				area_match = infobox_data[a]
				area_match = re.sub(r",|\(.*\)", "", area_match).strip()
				
				# {{convert|[number]|[km2 / sqmi]}}
				match = re.search(r"{{.*?\|([0-9]+)\s?\|(\w+).*?}}", area_match)
				if match:
					area = CoreUtils.convert_units(match.group(1), match.group(2), debugger)
					break
				
				# [number] [km2 / sqmi]
				split = area_match.split(" ")
				if len(split) > 1:
					area = CoreUtils.convert_units(split[0], split[1], debugger)
				else:
					try:
						number = float(area_match)
						area = str(number if number % 1 != 0 else int(number))
					except:
						debugger.log_message(f"error while converting area to float - {area}")
				break

		return area

	##
    # @brief extracts and assigns population from infobox
	@staticmethod
	def assign_population(infobox_data):
		population = ""
		
		if "population" in infobox_data and infobox_data["population"]:
			population_match = infobox_data["population"]
			population_match = re.sub(r",|\(.*\)", "", population_match).strip()
			
			if population_match.lower() == "uninhabited":
				population = "0"
				return population
			
			match = re.search(r"([0-9\.]+)\s+(\w+)", population_match)
			if match:
				#print(match.groups())
				if match.group(2) == "billion":
					population = round(float(match.group(1)) * 1e9)					
				# add more if needed
				return str(population)

			match = re.search(r"([0-9\.]+)", population)
			if match:
				population = match.group(1)

		return population			

	##
    # @brief assigns prefix based on infobox name
    #
    # geo:waterfall, geo:island, geo:relief, geo:peninsula or geo:continent
	@staticmethod
	def assign_prefix(infobox_name):
		prefix = "geo:"
		name = ""
		
		pattern = r"(waterfall|islands?|mountain|peninsulas?|continent)"
		match = re.search(pattern, infobox_name, re.I)
		if match:
			name = match.group(1).lower()

		if name in ("island", "islands"):
			prefix += "island"
		elif name == "mountain":
			prefix += "relief"
		elif name == "peninsulas":
			prefix += "peninsula"
		else:
			prefix += name

		return prefix

	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords

		return extracted