import re

from ent_core import EntCore

class EntWaterArea(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntWaterArea, self).__init__(title, prefix, link)

		self.continents = []
		self.latitude = ""
		self.longitude = ""
		self.area = ""

	def assign_values(self):
		print(self.title)
		self.assign_area()
		self.assign_lat_and_lon()
		# self.assign_country()

	def assign_lat_and_lon(self):
		possible_keys = ["coordinates", "coords"]
		for key in possible_keys: 
			if key in self.infobox_data:
				pattern = r"([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(N|S)\|([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(E|W)"
				match = re.search(pattern, self.infobox_data[key])
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
					print(f"{self.title}: did not match coords ({self.infobox_data[key]})")
				break

	def assign_area(self):
		if "area" in self.infobox_data:
			area = self.infobox_data['area']
			if area != "":
				# TODO
				print(area)
		else:
			print(f"{self.title}: area not found")

	def serialize(self):
		return f"{self.prefix}\t{self.title}\t{self.latitude}\t{self.longitude}\t{self.link}"

	@staticmethod
	def is_water_area(content):
		# check
		check = False

		pattern = r"{{[Ii]nfobox (?:body\sof\swater|sea)"
		match = re.search(pattern, content)
		if match:
			check = True
			
		return check
