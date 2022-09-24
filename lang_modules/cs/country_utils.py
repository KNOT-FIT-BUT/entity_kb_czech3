
import re

from lang_modules.cs.core_utils import CoreUtils

class CountryUtils:

	KEYWORDS = {
		"population": "počet obyvatel"
	}

	@staticmethod
	def assign_prefix(categories):
		# prefix - zaniklé státy
		content = "\n".join(categories)
		if re.search(r"Krátce\s+existující\s+státy|Zaniklé\s+(?:státy|monarchie)", content, re.I,):
			return "country:former"
		
		return "country"

	# TODO: aliases
	def assign_aliases(self):
		# aliases - czech name is preferable
		keys = ["název česky", "název_česky"]
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.del_redundant_text(self.infobox_data[key])
				self.aliases_infobox_cz.update(self.get_aliases(value, marked_czech=True))
				
				if len(self.aliases_infobox):
					self.aliases_infobox_orig.update(self.aliases_infobox)
					self.aliases_infobox.clear()
					if not len(self.aliases):
						self.first_alias = None
				break

		# aliases - common name may contain name in local language
		key = "název"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.del_redundant_text(self.infobox_data[key])
			aliases = self.get_aliases(value)
			
			if len(self.aliases_infobox_cz):
				var_aliases = self.aliases_infobox_orig
				if not len(self.aliases):
					self.first_alias = None
			else:
				var_aliases = self.aliases_infobox
			var_aliases.update(aliases)

		# jazyk pro oficiální nečeský název
		key = "iso2"
		if key in self.infobox_data and self.infobox_data[key]:
			value = self.infobox_data[key]
			self.lang_orig = value.lower()
	