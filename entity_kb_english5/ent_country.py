
import re
from ent_core import EntCore

class EntCountry(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntCountry, self).__init__(title, prefix, link)

		self.area = ""
		self.population = ""

	def assign_values(self):
		self.assign_area()
		self.assign_population()

	def assign_area(self):
		
		if "area_km2" in self.infobox_data:
			area = self.infobox_data['area_km2']
			area = area.replace(",", "")
			area = re.sub(r"\{\{.+\}\}", "", area)
			self.area = area

	def assign_population(self):
		pass

	def serialize(self):
		return f"{self.prefix}\t{self.title}\t{self.area}\t{self.link}"

	@staticmethod
	def is_country(content, tmp):
		
		# check
		pattern = r"\[\[Category:Countries\s+in\s+(?:Europe|Africa|Asia|Australia|Oceania|(?:South|North)\s+America)\]\]"
		match = re.search(pattern, content)
		if match:
			return 1
		
		pattern = r"\[\[Category:Member\s+states\s+of\s+(?:the\sUnited\sNations|the\sCommonwealth\sof\sNations|the\sEuropean\sUnion|NATO)\]\]"
		match = re.search(pattern, content)
		if match:
			return 1

		pattern = r"\[\[Category:States\s+(?:of\sthe\sUnited\sStates|with\slimited\srecognition)\]\]"
		match = re.search(pattern, content)
		if match:
			return 1

		#print(f"did not identify country\t{tmp}")
		return 0
