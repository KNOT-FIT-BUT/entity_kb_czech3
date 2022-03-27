import re

from ent_core import EntCore

class EntWaterArea(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntWaterArea, self).__init__(title, prefix, link)

		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.area = ""

	def __repr__(self):
		return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.continents}")

	def assign_values(self):
		self.assign_area()
		self.assign_coordinates()
		self.assign_continents()

	def assign_coordinates(self):
		possible_keys = ["coordinates", "coords"]
		for key in possible_keys: 
			if key in self.infobox_data and self.infobox_data[key] != "":
				coords = self.get_coordinates(self.infobox_data[key])
				if all(coords):
					self.latitude, self.longitude = coords
				break

	def assign_area(self):
		if "area" in self.infobox_data:
			area = self.infobox_data['area']
			if area != "":
				match = re.search(r"{{.*?\|([0-9]+)\|(\w+).*?}}", area)
				if match:
					if match.group(2) == "km2":
						self.area = match.group(1)
					elif match.group(2) == "sqmi":
						self.area = round(int(match.group(1)) * 2.589988)
				else:
					print(f"{self.title}: did not match area ({area})")
		else:
			print(f"{self.title}: area not found")

	def assign_continents(self):
		if "location" in self.infobox_data:
			location = self.infobox_data['location']
			if location != "":
				continents = ["Asia", "Africa", "Europe", "North America", "South America", "Australia", "Oceania", "Antarctica"]
				patterns = [r"Asia", r"Africa", r"Europe", r"North[^,]+America", r"South[^,]+America", r"Australia", r"Oceania", r"Antarctica"]
				curr_continents = []
				for i in range(len(continents)):
					match = re.search(patterns[i], location)
					if match:					
						curr_continents.append(continents[i])
				self.continents  = " | ".join(curr_continents)
				return

		print(f"{self.title}: did not find location")

	@staticmethod
	def is_water_area(content):
		# check
		check = False

		pattern = r"{{[Ii]nfobox (?:body\sof\swater|sea)"
		match = re.search(pattern, content)
		if match:
			check = True
			
		return check
