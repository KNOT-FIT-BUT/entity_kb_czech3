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
	def __init__(self, title, prefix, link, langmap, redirects, debugger):
		"""
        inicializuje třídu EntEvent
        """

		super(EntEvent, self).__init__(title, prefix, link, langmap, redirects, debugger)

		self.start_date = ""
		self.end_date = ""
		self.locations = ""
		self.type = ""

	def __repr__(self):
		"""
        serializuje parametry třídy EntEvent
        """
		return self.serialize(f"{self.start_date}\t{self.end_date}\t{self.locations}\t{self.type}")

	def assign_values(self):
		"""
        pokusí se extrahovat parametry z infoboxů
        """

		# self.d.log_infobox(self.infobox_data)

		self.assign_dates()
		self.assign_locations()
		self.assign_type()

	def assign_dates(self):
		keys = ["year", "Year", "start_date", "first_aired", "election_date"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.extract_date(data)
				self.d.log_message(data[0])

		keys = ["end_date"]

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				data = self.extract_date(data)
				self.d.log_message(data[0])

		keys = ["date", "Date"]
		
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				data = self.infobox_data[key]
				self.d.log_message(f"{key}: {data}")

	def assign_locations(self):		
		pass

	def assign_type(self):
		pass


	@staticmethod
	def is_event(content, title):
		"""
        na základě obsahu stránky určuje, zda stránka pojednává o události, či nikoliv
        parametry:
        content - obsah stránky
        návratové hodnoty: True / False
        """

		pattern = r"\[\[Category:.*?event.*?]]"
		if re.search(pattern, content):
			# print(title)			
			return True
			
		return False
