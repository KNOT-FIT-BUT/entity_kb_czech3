import re

from ent_core import EntCore

class EntGeo(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntGeo, self).__init__(title, prefix, link)

		self.continent = ""
		self.latitude = ""
		self.longitude = ""
		self.area = ""
		self.population = ""
		self.total_height = ""

	def __repr__(self):
		if self.prefix == "geo:waterfall":
			return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.total_height}")
		elif self.prefix == "geo:island":
			return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")
		elif self.prefix == "geo:continent":
			return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")

		return self.serialize(f"{self.latitude}\t{self.longitude}")

	def assign_values(self):
		self.assign_coordinates()
		if self.prefix == "geo:waterfall":
			# assign continent
			self.assign_height()
		elif self.prefix == "geo:island":
			self.assign_area()
			self.assign_population()		
		elif self.prefix == "geo:continent":
			self.assign_area()
			self.assign_population()

	def assign_coordinates(self):		
		if "coordinates" in self.infobox_data and self.infobox_data["coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords

	def assign_height(self):
		if "height" in self.infobox_data and self.infobox_data["height"] != "":
			height = self.infobox_data["height"]

			# match "{{convert }}" format
			match = re.search(r"{{(?:convert|cvt)\|([0-9]+)\|(\w+).*}}", height)
			if match:
				if match.group(2) == "m":
					self.total_height = match.group(1)
				elif match.group(2) == "ft":
					self.total_height = round(int(match.group(1)) / 3.2808, 2)
			else:
				height = re.sub(r"\(.*\)", "", height).strip()
				split = height.split(" ")
				if len(split) > 1:
					if split[1] == "m" or split[1] == "meters":
						self.total_height = split[0]
					elif split[1] == "ft" or split[1] == "feet":
						self.total_height = round(int(split[0]) / 3.2808, 2)
				else:
					match = re.search(r"([0-9]+)(\w+)", split[0])
					if match:
						if match.group(2) == "m":
							self.total_height = match.group(1)
						elif match.group(2) == "ft":
							self.total_height = round(int(match.group(1)) / 3.2808, 2)
	
	def assign_area(self):
		area_infoboxes = ["area_km2", "area"]
		for a in area_infoboxes:
			if a in self.infobox_data and self.infobox_data[a]:
				area = self.infobox_data[a]
				area = re.sub(r",|\(.*\)", "", area).strip()
				
				# {{convert|[number]|[km2 / sqmi]}}
				match = re.search(r"{{.*?\|([0-9]+)\|(\w+).*?}}", area)
				if match:
					if match.group(2) == "km2":
						self.area = str(float(match.group(1)))
					elif match.group(2) == "sqmi":
						self.area = round(float(match.group(1)) * 2.589988)
					break
				
				# [number] [km2 / sqmi]
				split = area.split(" ")
				if len(split) > 1:
					if split[1] == "km2":
						self.area = str(float(split[0]))
					elif split[1] == "sqmi":
						self.area = round(float(split[0]) * 2.589988)
				else:
					self.area = str(float(area))
				break

	def assign_population(self):
		if "population" in self.infobox_data and self.infobox_data["population"]:
			population = self.infobox_data["population"]
			population = re.sub(r",|\(.*\)", "", population).strip()
			
			if population.lower() == "uninhabited":
				self.population = 0
				return
			
			match = re.search(r"([0-9\.]+)\s+(\w+)", population)
			if match:
				print(match.groups())
				if match.group(2) == "billion":
					self.population = round(float(match.group(1)) * 1e9)
				# add more if needed
				return

			match = re.search(r"([0-9\.]+)", population)
			if match:
				self.population = match.group(1)			

	@staticmethod
	def is_geo(content):
		# check and change prefix
		check = False
		prefix = ""

		#pattern = r"{{[Ii]nfobox\s+(waterfall)"
		# mountain | mountain pass
		pattern = r"{{[Ii]nfobox\s+(waterfall|[Ii]slands?|[Mm]ountain|[Pp]eninsulas?|[Cc]ontinent)"
		match = re.search(pattern, content)
		if match:
			prefix = match.group(1).lower()
			check = True

		if prefix in ("island", "islands"):
			prefix = "island"
		if prefix == "mountain":
			prefix = "relief"
		if prefix == "peninsulas":
			prefix = "peninsula"

		return check, prefix
