##
# @file ent_settlement.py
# @brief contains EntSettlement class - entity used for settlements
#
# @section ent_information entity information
# - area
# - population
# - latitude
# - longtitude
# - country
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

import re

from ent_core import EntCore

from lang_modules.en.settlement_utils import SettlementUtils as EnUtils
from lang_modules.cs.settlement_utils import SettlementUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}


##
# @class EntSettlement
# @brief entity used for settlements
class EntSettlement(EntCore):
	##
    # @brief initializes the settlement entity
    # @param title - page title (entity name) <string>
    # @param prefix - entity type <string>
    # @param link - link to the wikipedia page <string>
    # @param data - extracted entity data (infobox data, categories, ...) <dictionary>
    # @param langmap - language abbreviations <dictionary>
    # @param redirects - redirects to the wikipedia page <array of strings>
    # @param sentence - first sentence of the page <string>
    # @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		super(EntSettlement, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		self.area = ""
		self.population = ""
		self.latitude = ""
		self.longitude = ""
		self.country = ""

	##
    # @brief serializes entity data for output (tsv format)
    # @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.country,
			self.latitude,
			self.longitude,
			self.area,
			self.population
		]
		return self.serialize("\t".join(data))

	##
    # @brief tries to assign entity information (calls the appropriate functions)
	def assign_values(self, lang):
		# lang_utils = utils[lang]
		# extraction = lang_utils.extract_text(extraction, ent_data, self.d)

		self.assign_country()
		self.latitude, self.longitude = self.core_utils.assign_coordinates(self)
		self.area = self.assign_area()
		self.assign_population()

	##
    # @brief extracts and assigns country from infobox
	def assign_country(self):
		def fix_country(country):
			if re.search(r"Čechy|Morava|Slezsko|CZE?", country):
				country = "Czech Republic"
			country = country.replace("\n", "")
			country = re.sub(r"\(.*?\)", "", country)
			country = re.sub(r"\{\{(?:nowrap|flagu?|country|flagcountry|vlajka\s+a\s+název)\|([^\|]+)(.*?)?\}\}", r"\1", country, flags=re.I)
			country = re.sub(r"\[\[.*?\|([^\|\[]*?)\]\]", r"\1", country)
			country = re.sub(r"\[|\]", "", country)
			country = re.sub(r"\{\{plainlist\|\s*\*\s*(.+?)\*.*", r"\1", country)
			country = re.sub(r"\{\{([^\|]+?)\}\}", r"\1", country)
			country = re.sub(r"\{\{.*?\}\}", "", country)
			country = country.replace(",", "").strip()
			return country

		# cs specific	
		if self.infobox_name in ["česká obec", "statutární město"]:
			self.country = "Czech Republic"
			return
		if self.infobox_name == "anglické město":
			self.country = "United Kingdom"
			return
		
		# subdivision_name
		data = self.get_infobox_data(utils[self.lang].KEYWORDS["country"])
		if data:
			data = fix_country(data)
			self.country = data
	
	##
    # @brief extracts and assigns population from infobox
	def assign_population(self):
		data = self.get_infobox_data(utils[self.lang].KEYWORDS["population"])
		if data:
			if re.search(r"plainlist", data, flags=re.I):
				return
			data = re.sub(r"&nbsp;", "", data)
			data = re.sub(r"(?<=\d)\s(?=\d)", "", data)
			coef = (
				1000000
				if re.search(r"mil\.?|mili[oó]n", data, re.I)
				else 1000
				if re.search(r"tis\.?|tis[ií]c", data, re.I)
				else 0
			)
			if coef:
				match = re.search(r"([\d,\.]+)", data)
				data = match.group(1)
				data = data.replace(",", ".")
				data = str(int(float(data) * coef))
			else:
				data = re.sub(r"[,\.]", "", data)
			data = re.sub(r"\{\{.*?\}\}", "", data)
			match = re.findall(r"\d+", data)
			if match:
				data = match[0]				
				self.population = data