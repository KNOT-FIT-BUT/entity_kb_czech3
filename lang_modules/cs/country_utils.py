
import re

class CountryUtils:
	@staticmethod
	def assign_prefix(categories):
		# prefix - zaniklé státy
		content = "\n".join(categories)
		if re.search(r"Krátce\s+existující\s+státy|Zaniklé\s+(?:státy|monarchie)", content, re.I,):
			return "country:former"
		
		return "country"
	