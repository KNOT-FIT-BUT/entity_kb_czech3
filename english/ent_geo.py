"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntGeo', která uchovává údaje o geografických entitách.
Poznámka: inspirováno projektem entity_kb_czech3
"""

import re

from ent_core import EntCore

class EntGeo(EntCore):
	"""
    třída určená pro vodní toky
    instanční atributy:
        title       	- jméno geografické entity
        prefix      	- prefix entity
        eid         	- ID entity
        link        	- odkaz na Wikipedii
        area			- rozloha
		populatio		- populace
		latitude		- zeměpisná šířka
		longtitude		- zeměpisná délka
		continent 		- kontinenty
		total_height 	- výška 
	"""
	def __init__(self, title, prefix, link):
		"""
        inicializuje třídu EntGeo
        """

		super(EntGeo, self).__init__(title, prefix, link)

		self.continent = ""
		self.latitude = ""
		self.longitude = ""
		self.area = ""
		self.population = ""
		self.total_height = ""

	def __repr__(self):
		"""
        serializuje parametry třídy EntGeo
        """
		if self.prefix == "geo:waterfall":
			return self.serialize(f"{self.continent}\t{self.latitude}\t{self.longitude}\t{self.total_height}")
		elif self.prefix == "geo:island":
			return self.serialize(f"{self.continent}\t{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")
		elif self.prefix == "geo:continent":
			return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")
		elif self.prefix == "geo:relief":
			return self.serialize(f"{self.continent}\t{self.latitude}\t{self.longitude}")

		return self.serialize(f"{self.latitude}\t{self.longitude}")

	def assign_values(self):
		"""
        pokusí se extrahovat parametry z infoboxů
        """
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
		"""
        pokusí se extrahovat souřadnice z infoboxů coords a coordinates
		využívá funkci get_coordinates třídy EntCore
        """
		if "coordinates" in self.infobox_data and self.infobox_data["coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords

	def assign_height(self):
		"""
        pokusí se extrahovat výšku z infoboxu height
		využívá funkce convert_units z entity core
        """
		if "height" in self.infobox_data and self.infobox_data["height"] != "":
			height = self.infobox_data["height"]

			# match "{{convert }}" format
			match = re.search(r"{{(?:convert|cvt)\|([0-9]+)\|(\w+).*}}", height)
			if match:
				self.total_height = self.convert_units(match.group(1), match.group(2))
			else:
				height = re.sub(r"\(.*\)", "", height).strip()
				split = height.split(" ")
				if len(split) > 1:
					self.total_height = self.convert_units(split[0], split[1])
				else:
					match = re.search(r"([0-9]+)(\w+)", split[0])
					if match:
						self.total_height = self.convert_units(match.group(1), match.group(2))			
	
	def assign_area(self):
		"""
        pokusí se extrahovat rozlohu z infoboxu area nebo area_km2
		využívá funkce convert_units z entity core
        """
		area_infoboxes = ["area_km2", "area"]
		for a in area_infoboxes:
			if a in self.infobox_data and self.infobox_data[a]:
				area = self.infobox_data[a]
				area = re.sub(r",|\(.*\)", "", area).strip()
				
				# {{convert|[number]|[km2 / sqmi]}}
				match = re.search(r"{{.*?\|([0-9]+)\|(\w+).*?}}", area)
				if match:
					self.area = self.convert_units(match.group(1), match.group(2))
					break
				
				# [number] [km2 / sqmi]
				split = area.split(" ")
				if len(split) > 1:
					self.area = self.convert_units(split[0], split[1])
				else:
					number = float(area)
					self.area = str(number if number % 1 != 0 else int(number))
				break

	def assign_population(self):
		"""
        pokusí se extrahovat populaci z infoboxu population
        """
		if "population" in self.infobox_data and self.infobox_data["population"]:
			population = self.infobox_data["population"]
			population = re.sub(r",|\(.*\)", "", population).strip()
			
			if population.lower() == "uninhabited":
				self.population = 0
				return
			
			match = re.search(r"([0-9\.]+)\s+(\w+)", population)
			if match:
				#print(match.groups())
				if match.group(2) == "billion":
					self.population = round(float(match.group(1)) * 1e9)
				# add more if needed
				return

			match = re.search(r"([0-9\.]+)", population)
			if match:
				self.population = match.group(1)			

	@staticmethod
	def is_geo(content, title):
		"""
        na základě obsahu stránky určuje, zda stránka pojednává o vodním toku, či nikoliv, přidává prefix
        parametry:
        content - obsah stránky
        návratové hodnoty: 
		True / False
		prefix - typ geografické entity
		TODO: přidat lepší poznávání geografických entit?
        """
		# check and change prefix
		check = False
		prefix = ""

		# check title
		bad_pages = ["history", "geography", "list"]
		for page in bad_pages:
			if page in title.lower():
				return False, None
		
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
