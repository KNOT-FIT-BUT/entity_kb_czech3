"""
Projekt: entity_kb_english5
Autor: Jan Kapsa (xkapsa00)
Popis souboru: Soubor obsahuje třídu 'EntOrganization', která uchovává údaje o organizacích.
"""

import re

from ent_core import EntCore

class EntOrganization(EntCore):
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
	def __init__(self, title, prefix, link, langmap, redirects, debugger):
		"""
        inicializuje třídu EntOrganization
        """

		super(EntOrganization, self).__init__(title, prefix, link, langmap, redirects, debugger)

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
		# self.d.log_infobox(self.infobox_data)

		self.assign_dates()
		self.assign_location()
		self.assign_type()

	def assign_dates(self):
		pass

	def assign_location(self):
		pass

	def assign_type(self):
		pass

	@staticmethod
	def is_organization(content, title):
		"""
        na základě obsahu stránky určuje, zda stránka pojednává o organizaci, či nikoliv
        parametry:
        content - obsah stránky
        návratové hodnoty: True / False
        """

		pattern = r"\[\[Category:.*?(?:organizations?|organized crime (?:gangs|groups)|compan(?:y|ies)).*?]]"
		if re.search(pattern, content):
			# print(title)			
			return True
			
		return False
