"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntWaterCourse', která uchovává údaje o vodních tocích.
Poznámka: inspirováno projektem entity_kb_czech3
"""

import re

from ent_core import EntCore

class EntWaterCourse(EntCore):
	"""
    třída určená pro vodní toky
    instanční atributy:
        title       - jméno vodní plochy
        prefix      - prefix entity
        eid         - ID entity
        link        - odkaz na Wikipedii
        area		- rozloha
		latitude	- zeměpisná šířka
		longtitude	- zeměpisná délka
		continents 	- kontinenty
		length 		- délka
		source_loc 	- lokace pramene
		streamflow 	- proudění
    """
	def __init__(self, title, prefix, link):
		"""
        inicializuje třídu EntWaterCourse
        """

		super(EntWaterCourse, self).__init__(title, prefix, link)

		self.continents = ""
		self.latitude = ""
		self.longitude = ""
		self.length = ""
		self.area = ""
		self.streamflow = ""
		self.source_loc = ""

	def __repr__(self):
		"""
        serializuje parametry třídy EntWaterCourse
        """
		return self.serialize(f"{self.continents}\t{self.latitude}\t{self.longitude}\t{self.length}\t{self.area}\t{self.streamflow}\t{self.source_loc}")

	def assign_values(self):
		"""
        pokusí se extrahovat parametry z infoboxů
        """
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
		"""
        pokusí se extrahovat souřadnice z infoboxů coords a coordinates
		využívá funkci get_coordinates třídy EntCore
        """
		# TODO: edit extraction - extract source coords
		if "mouth_coordinates" in self.infobox_data and self.infobox_data["mouth_coordinates"] != "":
			coords = self.get_coordinates(self.infobox_data["mouth_coordinates"])
			if all(coords):
				self.latitude, self.longitude = coords

	def assign_length(self):
		"""
        pokusí se extrahovat délku  z infoboxu length
		využívá funkce convert_units z entity core
        """
		# | length = {{convert|352|km|mi|abbr=on}}
		if "length" in self.infobox_data:
			length = self.infobox_data["length"]
			if length != "":
				match = re.search(r"{{(?:[Cc]onvert|cvt)\|([0-9.]+)\|(.+?)(?:\|.+?)?}}", length)
				if match:
					self.length = self.convert_units(match.group(1), match.group(2))
				return
		
		#print(f"{self.title}: did not find length")
		pass
		
	def assign_area(self):
		"""
        pokusí se extrahovat razlohu z infoboxu basin_size
		využívá funkce convert_units z entity core
        """
		# | basin_size        = {{convert|4506|km2|abbr=on}}
		if "basin_size" in self.infobox_data:
			area = self.infobox_data["basin_size"]
			if area != "":
				match = re.search(r"{{.*?\|([0-9.]+)\|(\w+).*?}}", area)
				if match:
					self.area = self.convert_units(match.group(1), match.group(2))
					return
				else:
					print(f"{self.title}: did not match area ({area})")
		
		#print(f"{self.title}: area empty or not found")
		pass

	def assign_streamflow(self):
		"""
        pokusí se extrahovat streamflow z infoboxu discharge1_avg
		využívá funkce convert_units z entity core
        """
		# | discharge1_avg     = {{convert|593000|cuft/s|m3/s|abbr=on}}
		if "discharge1_avg" in self.infobox_data:
			streamflow = self.infobox_data["discharge1_avg"]
			if streamflow != "":
				streamflow = streamflow.replace(",", ".")
				match = re.search(r"{{.*?\|([0-9.,]+)\|((?:\w|\/)+).*?}}", streamflow)
				if match:
					self.streamflow = self.convert_units(match.group(1), match.group(2))
				else:
					print(f"{self.title}: did not match streamflow ({streamflow})")
		
		#print(f"{self.title}: streamflow empty or not found")
		pass

	def assign_source_loc(self):
		"""
        pokusí se extrahovat lokaci pramene z infoboxu source1_location
        """
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
		"""
        na základě obsahu stránky určuje, zda stránka pojednává o vodním toku, či nikoliv
        parametry:
        content - obsah stránky
        návratové hodnoty: True / False
		TODO: přidat lepší poznávání vodních toků
        """
		# check
		check = False

		pattern = r"{{[Ii]nfobox river"
		match = re.search(pattern, content)
		if match:
			check = True
			
		return check
