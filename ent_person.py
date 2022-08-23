##
# @file ent_person.py
# @brief contains EntPerson class - entity used for people, artists and groups
#
# @section ent_information entity information
# person and person:fictional:
# - birth_date
# - birth_place
# - death_date
# - death_place 
# - gender
# - jobs
# - nationality
#
# person:artist
# - art_forms
# - urls
#
# person:group - same as person but the values are arrays separated by "|"
#
# @todo finish artist
# @todo add group extraction
#
# @author created by Jan Kapsa (xkapsa00)
# @date 15.07.2022

from ent_core import EntCore

from lang_modules.en.person_utils import PersonUtils as EnUtils
from lang_modules.cs.person_utils import PersonUtils as CsUtils

utils = {
	"en": EnUtils,
	"cs": CsUtils
}

##
# @class EntPerson
# @brief entity used for people, artists and groups
class EntPerson(EntCore):
	##
	# @brief initializes the person entity
	# @param title - page title (entity name) <string>
	# @param prefix - entity type <string>
	# @param link - link to the wikipedia page <string>
	# @param data - extracted entity data (infobox data, categories, ...) <dictionary>
	# @param langmap - language abbreviations <dictionary>
	# @param redirects - redirects to the wikipedia page <array of strings>
	# @param sentence - first sentence of the page <string>
	# @param debugger - instance of the Debugger class used for debugging <Debugger>
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		# vyvolání inicializátoru nadřazené třídy
		super(EntPerson, self).__init__(title, prefix, link, data, langmap, redirects, sentence, debugger)

		# inicializace údajů specifických pro entitu
		self.birth_date = ""
		self.birth_place = ""
		self.death_date = ""
		self.death_place = ""
		self.gender = ""
		self.jobs = ""
		self.nationality = ""
		
		# artist
		self.art_forms = ""
		self.urls = ""

	##
	# @brief serializes entity data for output (tsv format)
	# @return tab separated values containing all of entity data <string>
	def __repr__(self):
		data = [
			self.gender,
			self.birth_date,
			self.birth_place,
			self.death_date,
			self.death_place,
			self.jobs,
			self.nationality
		]
		return self.serialize("\t".join(data))
	
	##
	# @brief tries to assign entity information (calls the appropriate functions)
	#
	# this function is getting called from the main script after identification
	def assign_values(self, lang):
		lang_utils = utils[lang]

		ent_data = {
			"title": self.title,
			"sentence": self.first_sentence,
			"first_paragraph": self.first_paragraph,
			"infobox_data": self.infobox_data,
			"infobox_name": self.infobox_name,
			"categories": self.categories
		}

		extraction = lang_utils.extract_infobox(ent_data, self.d)
		extraction = lang_utils.extract_text(extraction, ent_data, self.d)

		self.prefix 		= extraction["prefix"]
		if extraction["aliases"]:
			self.aliases	= extraction["aliases"] if self.aliases == "" else f"{self.aliases}|{extraction['aliases']}"
		
		self.birth_date 	= extraction["birth_date"]
		self.birth_place 	= extraction["birth_place"]
		self.death_date 	= extraction["death_date"]
		self.death_place	= extraction["death_place"]
		self.gender 		= extraction["gender"]
		self.jobs 			= extraction["jobs"]
		self.nationality 	= extraction["nationality"]
		
		# artist
		self.art_forms 		= extraction["art_forms"]
		self.urls 			= extraction["urls"]
