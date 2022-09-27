
import re

class GeoUtils:
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
