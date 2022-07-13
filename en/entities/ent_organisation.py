"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntOrganization', která uchovává údaje o organizacích.
"""

import re

from ent_core import EntCore

class EntOrganisation(EntCore):
	"""
    třída určená pro organizace
    instanční atributy:
        title       - jméno organizace
        prefix      - prefix entity
        eid         - ID entity
        link        - odkaz na Wikipedii
        founded		- datum založení
		cancelled	- datum ukončení
		location	- lokace
		type 		- typ organizace
    """
	def __init__(self, title, prefix, link, data, langmap, redirects, debugger):
		"""
        inicializuje třídu EntOrganization
        """

		super(EntOrganisation, self).__init__(title, prefix, link, data, langmap, redirects, debugger)

		self.founded = ""
		self.cancelled = ""
		self.location = ""
		self.type = ""

	def __repr__(self):
		"""
        serializuje parametry třídy EntOrganization
        """
		return self.serialize(f"{self.founded}\t{self.cancelled}\t{self.location}\t{self.type}")

	def assign_values(self):
		"""
        pokusí se extrahovat parametry z infoboxů
        """

		self.assign_dates()
		self.assign_location()
		self.assign_type()

	def assign_dates(self):
		
		keys = ["formation", "foundation", "founded", "fouded_date", "established"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				date = self.extract_date(data)
				if len(date) >= 1:
					self.founded = date[0]
					break

		keys = ["defunct", "banned", "dissolved"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				date = self.extract_date(data)
				if len(date) >= 1:
					self.cancelled = date[0]
					break

		keys = ["active", "dates"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				splitter = '-'
				if '–' in data:
					splitter = '–'
				data = data.split(splitter)
				if len(data) == 2:
					date = self.extract_date(data[0])
					if self.founded == "":
						self.founded = date[0]
					date = self.extract_date(data[1])
					if self.cancelled == "":
						self.cancelled = date[0]
					break

	def assign_location(self):
		
		location = ""
		country = ""
		city = ""

		keys = ["location", "headquarters", "hq_location", "area"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.remove_templates(data)
				location = data
				break
		
		keys = ["location_country", "country", "hq_location_country"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.remove_templates(data)
				country = data
				break

		keys = ["location_city", "hq_location_city"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.remove_templates(data)
				city = data
				break

		if city != "" and country != "":
			self.location = f"{city}, {country}"
		else:
			if location != "":
				self.location = location
			elif country != "":
				self.location = country
			else:
				self.location = city

	def assign_type(self):
		if "type" in self.infobox_data and self.infobox_data["type"] != "":
			data = self.infobox_data["type"]
			data = self.remove_templates(data)
			self.type = data
			return

		if self.infobox_name != "":
			if self.infobox_name.lower() != "organization":
				self.type = self.infobox_name

	@staticmethod
	def remove_templates(data):
		data = re.sub(r"\{\{.*?\}\}", "", data)
		data = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", data)
		data = re.sub(r"\[|\]|'|\(\)", "", data)
		return data