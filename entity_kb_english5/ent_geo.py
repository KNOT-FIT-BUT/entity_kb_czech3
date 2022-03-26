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

	def assign_values(self):
		if self.prefix == "geo:waterfall":
			self.assign_lat_and_lon()
			# assign continent
			self.assign_height()
		elif self.prefix == "geo:island":
			self.assign_lat_and_lon()
			self.assign_area()
			self.assign_population()		
		elif self.prefix == "geo:mountain":
			self.assign_lat_and_lon()

	def assign_lat_and_lon(self):		
		if "coordinates" in self.infobox_data and self.infobox_data["coordinates"] != "":
			#print(self.infobox_data["coordinates"])
			pattern = r"([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(N|S)\|([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(E|W)"
			match = re.search(pattern, self.infobox_data["coordinates"])
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
				#print(f"{self.title}: did not match coords ({self.infobox_data['mouth_coordinates']})")
				pass

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
		if "area_km2" in self.infobox_data and self.infobox_data["area_km2"]:
			#print(f"{self.title}: {self.infobox_data['area_km2']}")
			area = self.infobox_data["area_km2"]
			self.area = self.infobox_data["area_km2"] 

	def assign_population(self):
		if "population" in self.infobox_data and self.infobox_data["population"]:
			population = self.infobox_data["population"]
			population = re.sub(r",|\(.*\)", "", population).strip()
			if population.lower() == "uninhabited":
				population = 0
			self.population = population

	def serialize(self):
		if self.prefix == "geo:waterfall":
			return f"{self.prefix}\t{self.title}\t{self.latitude}\t{self.longitude}\t{self.total_height}\t{self.link}"
		elif self.prefix == "geo:island":
			return f"{self.prefix}\t{self.title}\t{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}\t{self.link}"
		elif self.prefix == "geo:mountain":
			return f"{self.prefix}\t{self.title}\t{self.latitude}\t{self.longitude}\t{self.link}"
		
		return f"{self.prefix}\t{self.title}\t{self.link}"


	@staticmethod
	def is_geo(content):
		# check and change prefix
		check = False
		prefix = ""

		#pattern = r"{{[Ii]nfobox\s+(waterfall)"
		# mountain | mountain pass
		pattern = r"{{[Ii]nfobox\s+(waterfall|[Ii]slands?|[Mm]ountain)"
		match = re.search(pattern, content)
		if match:
			prefix = match.group(1).lower()
			check = True

		if prefix in ("island", "islands"):
			prefix = "island"

		return check, prefix
