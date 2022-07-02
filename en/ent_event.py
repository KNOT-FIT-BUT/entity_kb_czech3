"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntEvent', která uchovává údaje o událostích.
"""

import re

from ent_core import EntCore

class EntEvent(EntCore):
	"""
    třída určená pro události
    instanční atributy:
        title       - jméno události
        prefix      - prefix entity
        eid         - ID entity
        link        - odkaz na Wikipedii
        start date	- datum začátku
		end date	- datum ukončení
		locations	- lokace
		type 		- typ události
    """
	def __init__(self, title, prefix, link, data, langmap, redirects, debugger):
		"""
        inicializuje třídu EntEvent
        """

		super(EntEvent, self).__init__(title, prefix, link, data, langmap, redirects, debugger)

		self.start_date = ""
		self.end_date = ""
		self.locations = []
		self.type = ""

	def __repr__(self):
		"""
        serializuje parametry třídy EntEvent
        """
		return self.serialize(f"{self.start_date}\t{self.end_date}\t{'|'.join(self.locations)}\t{self.type}")

	def assign_values(self):
		"""
        pokusí se extrahovat parametry z infoboxů
        """

		# arr = [
		# 	"place", 
		# 	"cities",
		# 	"host_city",
		# 	"affected",
		# 	"country",
		# 	"location",
		# 	"Location"
		# 	"Areas",
		# 	"city",
		# 	"venue",
		# 	"site"
		# ]
		# found = False

		# for item in arr:
		# 	if item in self.infobox_data and item != "":
		# 		found = True
		# 		break
		# if not found:
		# 	self.d.log_infobox(self.infobox_data)

		self.assign_dates()
		self.assign_locations()
		self.assign_type()

	def assign_dates(self):
		keys = ["year", "Year", "start_date", "first_aired", "election_date"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.extract_date(data)
				self.start_date = data[0]

		keys = ["end_date"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.extract_date(data)
				self.end_date = data[0]

		keys = ["date", "Date"]
		
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				split = data.split("–")
				split = [item.strip() for item in split if item != ""]
				if len(split) == 1:
					date = self.extract_date(split[0])
					if len(date) == 1:
						self.start_date = date[0]
					else:
						self.start_date = date[0]
						self.end_date = date[1]
					break
				else:
					
					# 19-25 September 2017 -> 19 September 2017 - 25 September 2017
					if re.search(r"^[0-9]+$", split[0]):
						match = re.search(r"^[0-9]+?\s+?([a-z]+?\s+?[0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return

					# January-September 2017 -> January 2017 - September 2017
					if re.search(r"^[a-z]+$", split[0], re.I):
						match = re.search(r"^[a-z]+?\s+?([0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return

					self.start_date = self.extract_date(split[0])[0]
					self.end_date = self.extract_date(split[1])[0]

	def assign_locations(self):		
		keys = [
			"place", 
			"country",
			"location",
			"Location",
			"Areas",
			"city",
			"host_city",
			"cities",
			"affected",
			"site",
			"venue"
		]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.remove_templates(data)
				
				if re.search(r"[a-z][A-Z]", data):
					string = re.sub(r"([a-z])([A-Z])", r"\1|\2", data)
					split = string.split("|")
					found = False
					for s in split:
						if "," not in s:
							found = True
							break
					if found:
						string = re.sub(r"([a-z])([A-Z])", r"\1, \2", data)
						self.locations.append(string)
					else:
						self.locations = split
					break
				
				if "," in data:
					split = data.split(",") 
					if len(split) > 5:
						self.locations = [item.strip() for item in split]
						break

				self.locations.append(data)
				break

	def assign_type(self):
		
		type = ""
		name = ""

		if "type" in self.infobox_data and self.infobox_data["type"] != "":
			type = self.infobox_data["type"]
			type = self.remove_templates(type).lower()

		if self.infobox_name != "" and self.infobox_name != "event":
			name = self.infobox_name.lower()

		if name == "election" and type != "":
			self.type = f"{type} election"
			return
		else:
			self.type = "election"

		if type != "":
			self.type = type
		else:
			self.type = name

	@staticmethod
	def remove_templates(data):
		data = re.sub(r"\{\{.*?\}\}", "", data)
		data = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", data)
		data = re.sub(r"\[|\]|'|\(\)", "", data)
		return data

