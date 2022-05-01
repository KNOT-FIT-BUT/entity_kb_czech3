"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntWaterArea', která uchovává údaje o vodních plochách.
Poznámka: inspirováno projektem entity_kb_czech3
"""

import re

from ent_core import EntCore

class EntWaterArea(EntCore):
	"""
    třída určená pro vodní plochy
    instanční atributy:
        title       - jméno vodní plochy
        prefix      - prefix entity
        eid         - ID entity
        link        - odkaz na Wikipedii
        area		- rozloha
		latitude	- zeměpisná šířka
		longtitude	- zeměpisná délka
		continents 	- kontinenty
    """
	def __init__(self, title, prefix, link, langmap, redirects):
		"""
        inicializuje třídu EntWaterArea
        """

		super(EntWaterArea, self).__init__(title, prefix, link, langmap, redirects)

		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.area = ""

	def __repr__(self):
		"""
        serializuje parametry třídy EntWaterArea
        """
		return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.continents}")

	def assign_values(self):
		"""
        pokusí se extrahovat parametry z infoboxů
        """
		self.assign_area()
		self.assign_coordinates()
		self.assign_continents()

	def assign_coordinates(self):
		"""
        pokusí se extrahovat souřadnice z infoboxů coords a coordinates
		využívá funkci get_coordinates třídy EntCore
        """
		possible_keys = ["coordinates", "coords"]
		for key in possible_keys: 
			if key in self.infobox_data and self.infobox_data[key] != "":
				coords = self.get_coordinates(self.infobox_data[key])
				if all(coords):
					self.latitude, self.longitude = coords
				return
		
		if self.coords != "":
			coords = self.get_coordinates(self.coords)
			if all(coords):
				self.latitude, self.longitude = coords

	def assign_area(self):
		"""
        pokusí se extrahovat rozlohu z infoboxu area
        """
		if "area" in self.infobox_data:
			area = self.infobox_data['area']
			if area != "":
				match = re.search(r"{{.*?\|([0-9\.]+)\|(\w+).*?}}", area)
				if match:
					self.area = self.convert_units(match.group(1), match.group(2))
				else:
					#print(f"{self.title}: did not match area ({area})")
					pass
		else:
			#print(f"{self.title}: area not found")
			pass

	def assign_continents(self):
		"""
        pokusí se extrahovat kontinenty z infoboxu location
        """
		if "location" in self.infobox_data:
			location = self.infobox_data['location']
			if location != "":
				continents = ["Asia", "Africa", "Europe", "North America", "South America", "Australia", "Oceania", "Antarctica"]
				patterns = [r"Asia", r"Africa", r"Europe", r"North[^,]+America", r"South[^,]+America", r"Australia", r"Oceania", r"Antarctica"]
				curr_continents = []
				for i in range(len(continents)):
					match = re.search(patterns[i], location)
					if match:					
						curr_continents.append(continents[i])
				self.continents  = "|".join(curr_continents)
				return

		#print(f"{self.title}: did not find location")
		pass

	@staticmethod
	def is_water_area(content, title):
		"""
        na základě obsahu stránky určuje, zda stránka pojednává o vodní ploše, či nikoliv
        parametry:
        content - obsah stránky
        návratové hodnoty: True / False
        """

		pattern = r"{{[Ii]nfobox (?:body\sof\swater|sea)"
		if re.search(pattern, content):
			return True

		# lake in name but no infobox
		# TODO: could be wrong (e.g.: Meadow Lake Airport)
		if "lake" in title.lower() and not "lakes" in title.lower():
			return True
			
		return False
