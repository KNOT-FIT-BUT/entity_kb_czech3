
import re

from ent_core import EntCore

class EntCountry(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntCountry, self).__init__(title, prefix, link)

		self.area = ""
		self.population = ""
		self.latitude = ""
		self.longitude = ""

	def __repr__(self):
		return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")

	def assign_values(self):
		self.assign_area()
		self.assign_population()
		self.assign_coordinates()

	def assign_coordinates(self):
		if "coordinates" in self.infobox_data and self.infobox_data["coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords	

	def assign_area(self):
		
		if "area_km2" in self.infobox_data:
			area = self.infobox_data['area_km2']
			area = area.replace(",", "")
			area = re.sub(r"\{\{.+\}\}", "", area)
			self.area = area

	def assign_population(self):
		
		# population_census
		# population_estimate

		if "population_estimate" in self.infobox_data:
			if self.infobox_data["population_estimate"] != "":
				#print(f"{self.title}: estimate {self.infobox_data['population_estimate']}")				
				match = re.findall(r"[0-9,]+", self.infobox_data["population_estimate"])
				if match:
					self.population = match[0].replace(',','')
					return

		if "population_census" in self.infobox_data:
			if self.infobox_data["population_census"] != "":
				#print(f"{self.title}: census {self.infobox_data['population_census']}")
				match = re.findall(r"[0-9,]+", self.infobox_data["population_census"])
				if match:
					self.population = match[0].replace(',','')
					return				
		
		else: 
			print(f"{self.title}: population not found")

	@staticmethod
	def is_country(content):
		
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
			
		return 0
