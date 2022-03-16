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

	def assign_values(self):
		self.assign_area()
		self.assign_population()
		self.assign_lat_and_lon()
		self.assign_country()

	def assign_lat_and_lon(self):
		if "coordinates" in self.infobox_data:
			pattern = r"([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(N|S)\|([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(E|W)"
			match = re.search(pattern, self.infobox_data['coordinates'])
			if match:
				# converting to longtitude and latitude
				groups = [x for x in match.groups() if x is not None]
				lat_n = 0
				lon_n = 0
				lat_d = ""
				lon_d = ""
				lat = []
				lon = []
				switch = False
				lon_d = groups[-1]
				for group in groups[:-1]:
					if switch == False:
						if group == "N" or group == "S":
							lat_d = group
							switch = True
						else:
							lat.append(group)
					else:
						lon.append(group)

				# calculation
				for i in range(len(lat)):
					if i == 0:
						lat_n += float(lat[i])
					else:
						lat_n += float(lat[i]) / 60 * i
				for i in range(len(lon)):
					if i == 0:
						lon_n += float(lon[i])
					else:
						lon_n += float(lon[i]) / 60 * i
				
				# * direction
				if lat_d == "S":
					lat_n = -lat_n
				lat_n = round(lat_n, 5)
				if lon_d == "W":
					lon_n = -lon_n
				lon_n = round(lon_n, 5)

				self.latitude = lat_n
				self.longitude = lon_n
			else:
				print(f"{self.title}: did not match coords ({self.infobox_data['coordinates']})")
		# else:
		# 	print(f"{self.title}: coords not found")	

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

	def serialize(self):
		return f"{self.prefix}\t{self.title}\t{self.country}\t{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}\t{self.link}"

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
