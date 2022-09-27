
import re

class CountryUtils:
	
	@staticmethod
	def assign_prefix(categories):
		for category in categories:
			# TODO: "developed" is too specific
			if "developed" in category:
				continue
			if re.search(r"former.*?countries", category.lower(), re.I):
				return "country:former"
		return "country"
