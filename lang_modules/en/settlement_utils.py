
import re

from lang_modules.en.core_utils import CoreUtils

class SettlementUtils:

	KEYWORDS = {
		"population": "population_total",
		"country": "subdivision_name"
	}

	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords

		return extracted