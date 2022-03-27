import re

from ent_core import EntCore

class EntSettlement(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntSettlement, self).__init__(title, prefix, link)

		self.area = ""
		self.population = ""
		self.latitude = ""
		self.longitude = ""
		self.country = ""

	def __repr__(self):
		return self.serialize(f"{self.country}\t{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")

	def assign_values(self):
		self.assign_area()
		self.assign_population()
		self.assign_coordinates()
		self.assign_country()

	def assign_coordinates(self):
		if "coordinates" in self.infobox_data and self.infobox_data["coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords

	def assign_area(self):
		
		if "area_total_km2" in self.infobox_data:
			area = self.infobox_data['area_total_km2']
			area = area.replace(",", "")
			area = re.sub(r"\{\{.+\}\}", "", area)
			self.area = area
		# else:
		# 	print(f"{self.title}: area not found")

	def assign_population(self):
		
		# population_total

		if "population_total" in self.infobox_data:
			if self.infobox_data["population_total"] != "":
				match = re.findall(r"[0-9,]+", self.infobox_data["population_total"])
				if match:
					self.population = match[0].replace(',','')
					return
		# else: 
		# 	print(f"{self.title}: population not found")

	def assign_country(self):
		# subdivision_name
		if "subdivision_name" in self.infobox_data:
			if self.infobox_data["subdivision_name"] != "":
				country = self.infobox_data["subdivision_name"]  
				country = re.sub(r"\[|\]|\{|\}", "", country, flags=re.DOTALL)
				split = country.split("|")
				if len(split) > 1:
					country = split[-1]
				self.country = country
		# else: 
		# 	print(f"{self.title}: country not found")	

	@staticmethod
	def is_settlement(content):
		# check
		check = False

		# infobox name = settlement
		pattern = r"{{[Ii]nfobox settlement"
		match = re.search(pattern, content)
		if match:
			check = True

		# categories
		# pattern = r"\[\[Category:\s?(?:[cC]ities|[tT]owns|[vV]illages|.*?[pP]opulated\splaces).*?\]\]"
		# match = re.search(pattern, content)
		# if match:
		# 	return 1
			
		return check
