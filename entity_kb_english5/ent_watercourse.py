from nis import match
import re

from ent_core import EntCore

class EntWaterCourse(EntCore):
	
	def __init__(self, title, prefix, link):
		super(EntWaterCourse, self).__init__(title, prefix, link)

		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.length = ""
		self.area = ""
		self.streamflow = ""
		self.source_loc = ""

	def __repr__(self):
		return self.serialize(f"{self.continents}\t{self.latitude}\t{self.longitude}\t{self.length}\t{self.area}\t{self.streamflow}\t{self.source_loc}")

	def assign_values(self):
		#print(self.title)
		# self.assign_continents()
		self.assign_coordinates()
		self.assign_length()
		self.assign_area()
		self.assign_streamflow()
		self.assign_source_loc()	

	def assign_continents(self):
		# cant match from infobox
		pass

	def assign_coordinates(self):
		# TODO: edit extraction - extract source coords
		if "mouth_coordinates" in self.infobox_data and self.infobox_data["mouth_coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["mouth_coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords

	def assign_length(self):
		# | length = {{convert|352|km|mi|abbr=on}}
		if "length" in self.infobox_data:
			length = self.infobox_data["length"]
			if length != "":
				match = re.search(r"{{(?:[Cc]onvert|cvt)\|([0-9.]+)\|(.+?)(?:\|.+?)?}}", length)
				if match:
					if match.group(2) == "km":
						self.length = match.group(1)
					elif match.group(2) == "mi":
						self.length = round(int(match.group(1) * 1.609344), 2)
					else:
						print(f"{self.title}: length error ({match.group(2)})")
				return
		
		#print(f"{self.title}: did not find length")
		pass
		
	def assign_area(self):
		# | basin_size        = {{convert|4506|km2|abbr=on}}
		if "basin_size" in self.infobox_data:
			area = self.infobox_data["basin_size"]
			if area != "":
				match = re.search(r"{{.*?\|([0-9.]+)\|(\w+).*?}}", area)
				if match:
					if match.group(2) == "km2":
						self.area = match.group(1)
					elif match.group(2) == "sqmi":
						self.area = round(int(match.group(1)) * 2.589988)
					else:
						print(f"{self.title}: area error ({match.group(2)})")
					return
				else:
					print(f"{self.title}: did not match area ({area})")
		
		#print(f"{self.title}: area empty or not found")
		pass

	def assign_streamflow(self):
		# | discharge1_avg     = {{convert|593000|cuft/s|m3/s|abbr=on}}
		if "discharge1_avg" in self.infobox_data:
			streamflow = self.infobox_data["discharge1_avg"]
			if streamflow != "":
				streamflow = streamflow.replace(",", ".")
				match = re.search(r"{{.*?\|([0-9.,]+)\|((?:\w|\/)+).*?}}", streamflow)
				if match:
					if match.group(2) == "m3/s" or match.group(2) == "m3":
						self.streamflow = match.group(1)
					elif match.group(2) == "cuft/s" or match.group(2) == "cuft":
						self.streamflow = round(int(match.group(1)) * 0.028317, 2)
					else:
						print(f"{self.title}: streamflow error ({match.group(2)})")
					return
				else:
					print(f"{self.title}: did not match streamflow ({streamflow})")
		
		#print(f"{self.title}: streamflow empty or not found")
		pass

	def assign_source_loc(self):
		# format: source1_location = near [[Hollenthon, Austria|Hollenthon]], [[Lower Austria]]
		if "source1_location" in self.infobox_data:
			source = self.infobox_data["source1_location"]
			if source != "":
				source = re.sub(r"\[\[([^\]]+?)\|([^\]]+?)\]\]", r"\2", source)
				source = re.sub(r"{{[^}]+?\|([^}]+?)(?:\|[^}]+?)?}}", r"\1", source)
				source = re.sub(r"\[|\]|\'", "", source)
				self.source_loc = source
				return
		
		#print(f"{self.title}: did not found source location")
		pass

	@staticmethod
	def is_water_course(content):
		# check
		check = False

		pattern = r"{{[Ii]nfobox river"
		match = re.search(pattern, content)
		if match:
			check = True
			
		return check
