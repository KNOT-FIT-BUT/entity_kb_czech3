
import re
from lang_modules.cs.core_utils import CoreUtils

class GeoUtils:

	KEYWORDS = {
		"height": ["celková výška", "celková_výška"],
		"population": ["počet obyvatel", "počet_obyvatel"]
	}
	
	@staticmethod
	def assign_prefix(geo):
		if (re.search(r"poloostrovy\s+(?:na|ve?)", "\n".join(geo.categories), re.I)
				or re.search(r"poloostrov", geo.original_title, re.I)):
			return "geo:peninsula"
		elif (geo.infobox_name in ["reliéf", "hora", "průsmyk", "pohoří", "sedlo"] 
				or re.search(r"reliéf|hora|průsmyk|pohoří|sedlo", geo.original_title, re.I)):
			return "geo:relief"
		elif (geo.infobox_name == "kontinent"
				or re.search(r"kontinent", geo.original_title, re.I)):
			return "geo:continent"
		elif (geo.infobox_name == "ostrov"
				or re.search(r"ostrov", geo.original_title, re.I)):
			return "geo:island"
		elif (geo.infobox_name == "vodopád"
				or re.search(r"vodopád", geo.original_title, re.I)):
			return "geo:waterfall"
		else:
			return "geo:unknown"

	@staticmethod
	def get_coef(value):
		if re.search(r"mil\.|mili[oó]n", value, re.I):
			return 10e6
		if re.search(r"tis\.|tis[ií]c", value, re.I):
			return 10e3
		return 1
