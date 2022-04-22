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

	def assign_area(self):
		"""
        pokusí se extrahovat rozlohu z infoboxu area_km2
		TODO (TEST): přidat více infoboxů? (země využívající imperiální jednotky)
        """
		if "area_km2" in self.infobox_data:
			area = self.infobox_data['area_km2']
			area = area.replace(",", "")
			area = re.sub(r"\{\{.+\}\}", "", area)
			self.area = area

	def assign_population(self):
		"""
        pokusí se extrahovat populaci z infoboxů population_estimate a population_census 
		(pokud není nalezen estimate)
        """

		# population_estimate
		if "population_estimate" in self.infobox_data:
			if self.infobox_data["population_estimate"] != "":
				#print(f"{self.title}: estimate {self.infobox_data['population_estimate']}")				
				match = re.findall(r"[0-9,]+", self.infobox_data["population_estimate"])
				if match:
					self.population = match[0].replace(',','')
					return
		
		# population_census
		if "population_census" in self.infobox_data:
			if self.infobox_data["population_census"] != "":
				#print(f"{self.title}: census {self.infobox_data['population_census']}")
				match = re.findall(r"[0-9,]+", self.infobox_data["population_census"])
				if match:
					self.population = match[0].replace(',','')
					return	

		#print(f"{self.title}: population not found")
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
		match = re.search(pattern, content)
		if match:
			return True
		
		pattern = r"\[\[Category:Member\s+states\s+of\s+(?:the\sUnited\sNations|the\sCommonwealth\sof\sNations|the\sEuropean\sUnion|NATO)\]\]"
		match = re.search(pattern, content)
		if match:
			return True

		pattern = r"\[\[Category:States\s+(?:of\sthe\sUnited\sStates|with\slimited\srecognition)\]\]"
		match = re.search(pattern, content)
		if match:
			return True

		pattern = r"\[\[Category:States\s+(?:of\sthe\sUnited\sStates|with\slimited\srecognition)\]\]"
		match = re.search(pattern, content)
		if match:
			return True

		# TODO: categories or infobox?
		pattern = r"\[\[Category:.*?former.*?countries.*?\]\]"
		#pattern = r"{{Infobox former country"
		match = re.search(pattern, content, re.I)
		if match:
			return True
			
		return False
