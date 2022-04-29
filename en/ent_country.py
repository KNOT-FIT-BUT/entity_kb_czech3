"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntCountry', která uchovává údaje o zemích.
Poznámka: inspirováno projektem entity_kb_czech3
"""

import re

from ent_core import EntCore

class EntCountry(EntCore):
	"""
    třída určená pro země
    instanční atributy:
        title       - jméno země
        prefix      - prefix entity
        eid         - ID entity
        link        - odkaz na Wikipedii
        area		- rozloha
		population	- populace	
		latitude	- zeměpisná šířka
		longtitude	- zeměpisná délka
    """
	def __init__(self, title, prefix, link, langmap, redirects):
		"""
        inicializuje třídu EntCountry
        """

		super(EntCountry, self).__init__(title, prefix, link, langmap, redirects)

		self.area = ""
		self.population = ""
		self.latitude = ""
		self.longitude = ""

	def __repr__(self):
		"""
        serializuje parametry třídy EntCounry
        """
		return self.serialize(f"{self.latitude}\t{self.longitude}\t{self.area}\t{self.population}")

	def assign_values(self):
		"""
        pokusí se extrahovat parametry z infoboxů
        """

		for category in self.categories:
			# TODO: "developed" is too specific
			if "developed" in category:
				continue
			if re.search(r"former.*?countries", category.lower(), re.I):
				self.prefix += ":former"
				break

		self.assign_area()
		self.assign_population()
		self.assign_coordinates()

	def assign_coordinates(self):
		"""
        pokusí se extrahovat souřadnice z infoboxu coordinates
		využívá funkci get_coordinates třídy EntCore
        """
		if "coordinates" in self.infobox_data and self.infobox_data["coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords
				return

		if self.coords != "":
			coords = self.get_coordinates(self.coords)
			if all(coords):
				self.latitude, self.longitude = coords

	def assign_area(self):
		"""
        pokusí se extrahovat rozlohu z infoboxu area_km2
		TODO (TEST): přidat více infoboxů? (země využívající imperiální jednotky)
        """
		names = ("area_km2", "area_total_km2")
		for name in names:
			if name in self.infobox_data and self.infobox_data[name] != "":
				area = self.infobox_data[name]
				area = area.replace(",", "")
				area = re.sub(r"\{\{.+\}\}", "", area)
				self.area = area
				return

		names = ("area_sq_mi", "area_total_sq_mi")
		for name in names:
			if name in self.infobox_data and self.infobox_data[name] != "":
				area = self.infobox_data[name]
				area = area.replace(",", "")
				area = re.sub(r"\{\{.+\}\}", "", area)
				self.area = self.convert_units(area, "sqmi")
				return

		if self.prefix != "country:former":
			#print(f"\n{self.link}")
			pass

	def assign_population(self):
		"""
        pokusí se extrahovat populaci z infoboxů population_estimate a population_census 
		(pokud není nalezen estimate)
        """

		names = ("population_estimate", "population_census")
		for name in names:
			if name in self.infobox_data and self.infobox_data[name] != "":
				#print(f"{self.title}: estimate {self.infobox_data['population_estimate']}")				
				match = re.findall(r"[0-9,]+", self.infobox_data[name])
				if match:
					self.population = match[0].replace(',','')
					return
		
		# if self.prefix != "country:former":
		# 	print(f"\n{self.title}: population not found ({self.link})")
		pass

	@staticmethod
	def is_country(content, title):
		"""
        na základě obsahu stránky určuje, zda stránka pojednává o zemi, či nikoliv
        parametry:
        content - obsah stránky
        návratové hodnoty: True / False
        """

		# check title
		bad_pages = ["history", "geography", "list"]
		for page in bad_pages:
			if page in title.lower():
				return False

		# check categories
		pattern = r"\[\[Category:Countries\s+in\s+(?:Europe|Africa|Asia|Australia|Oceania|(?:South|North)\s+America)\]\]"
		if re.search(pattern, content):
			return True
		
		pattern = r"\[\[Category:Member\s+states\s+of\s+(?:the\sUnited\sNations|the\sCommonwealth\sof\sNations|the\sEuropean\sUnion|NATO)\]\]"
		if re.search(pattern, content):
			return True

		pattern = r"\[\[Category:States\s+(?:of\sthe\sUnited\sStates|with\slimited\srecognition)\]\]"	
		if re.search(pattern, content):
			return True

		pattern = r"\[\[Category:States\s+(?:of\sthe\sUnited\sStates|with\slimited\srecognition)\]\]"
		if re.search(pattern, content):
			return True

		# TODO: categories or infobox?
		#pattern = r"{{Infobox former country"
		pattern = r"\[\[Category:.*?former.*?countries.*?\]\]"
		if re.search(pattern, content, re.I):
			return True
			
		return False