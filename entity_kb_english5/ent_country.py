
import re
from unicodedata import decimal
#import requests

from ent_core import EntCore

# WIKI_API_URL = "https://cs.wikipedia.org/w/api.php"
# WIKI_API_PARAMS_BASE = {
#     "action": "query",
#     "format": "json",
# }


class EntCountry(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntCountry, self).__init__(title, prefix, link)

		self.area = ""
		self.population = ""
		self.latitude = 0
		self.longitude = 0

	def assign_values(self):
		self.assign_area()
		self.assign_population()
		self.assign_lat_and_lon()
		# self.get_wiki_api_location()
		
	# def get_wiki_api_location(self):
	# 	wiki_api_params = WIKI_API_PARAMS_BASE.copy()
	# 	wiki_api_params["prop"] = "coordinates"
	# 	wiki_api_params["titles"] = self.title
	# 	try:
	# 		r = requests.get(WIKI_API_URL, params=wiki_api_params)
	# 		pages = r.json()["query"]["pages"]
	# 		first_page = next(iter(pages))
	# 		if first_page != "-1":
	# 			self.latitude = pages[first_page]["coordinates"][0]["lat"]
	# 			self.longitude = pages[first_page]["coordinates"][0]["lon"]
	# 			print(f"{self.title}: {self.latitude}, {self.longitude}")				
	# 	except Exception as e:
	# 		self.latitude = ""
	# 		self.longitude = ""

	def assign_lat_and_lon(self):
		if "coordinates" in self.infobox_data:
			#print(f"{self.title}: {self.infobox_data['coordinates']}")
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

	def serialize(self):
		return f"{self.prefix}\t{self.title}\t{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}\t{self.link}"

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
