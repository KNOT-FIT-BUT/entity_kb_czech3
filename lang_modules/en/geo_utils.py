
import re

from lang_modules.en.core_utils import CoreUtils

class GeoUtils:

	KEYWORDS = {
		"height": ["height"]
	}

	##
    # @brief assigns prefix based on infobox name
    #
    # geo:waterfall, geo:island, geo:relief, geo:peninsula or geo:continent
	@staticmethod
	def assign_prefix(geo):
		prefix = "geo:"
		name = ""
		
		pattern = r"(waterfall|islands?|mountain|peninsulas?|continent)"
		match = re.search(pattern, geo.infobox_name, re.I)
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
	def get_coef(value):
		if re.search(r"billion", value, flags=re.I):
			return 10e9
		return 1

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

	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords

		return extracted

