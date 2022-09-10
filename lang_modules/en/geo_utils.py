
import re

from lang_modules.en.core_utils import CoreUtils

class GeoUtils:

	KEYWORDS = {
		"height": "height",
		"population": "population"
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

	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords

		return extracted

