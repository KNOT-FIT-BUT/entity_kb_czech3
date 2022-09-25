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

import re

from debugger import Debugger as debug

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
		self.prefix = utils[lang].assign_prefix(self)
		self.birth_date, self.death_date = utils[lang].assign_dates(self)
		self.assign_places()
		self.assign_gender()
		self.assign_jobs()
		self.assign_nationality()

		self.extract_text()

		# artist
		if self.prefix == "person:artist":
			self.assign_art_forms()
			self.assign_urls()

	##
	# @brief extracts and assigns places from infobox, removes wikipedia formatting
	def assign_places(self):
		def fix_place(place):
			p = re.sub(r"{{Vlajka a název\|(.*?)(?:\|.*?)?}}", r"\1", place, flags=re.I)
			p = re.sub(r"{{flagicon\|(.*?)(?:\|.*?)?}}", r"\1", p, flags=re.I)
			p = re.sub(r"{{(?:malé|small)\|(.*?)}}", r"\1", p, flags=re.I)
			p = re.sub(r"{{nowrap\|(.*?)}}", r"\1", p)
			p = re.sub(r"\[\[(?:file|soubor|image):.*?\]\]", "", p, flags=re.I)
			p = re.sub(r"\{\{.*?\}\}", "", p)
			p = re.sub(r"\[\[[^]]*?\|([^\|]*?)\]\]", r"\1", p)
			p = re.sub(r"\[|\]", "", p)
			p = re.sub(r"\s+", " ", p)
			return p.strip()

		value = self.get_infobox_data(utils[self.lang].KEYWORDS["birth_place"])
		if value:
			birth_place = fix_place(value)
			self.birth_place = birth_place

		value = self.get_infobox_data(utils[self.lang].KEYWORDS["birth_place"])
		if value:
			death_place = fix_place(value)
			self.death_place = death_place

	##	
	# @brief extracts and assigns gender
	def assign_gender(self):
		# infobox search
		value = self.get_infobox_data(utils[self.lang].KEYWORDS["gender"])
		if value:
			value = value.lower().strip()
			value = re.sub(r"\(.*?\)", "", value).strip()			
			if value in utils[self.lang].KEYWORDS["male"]:
				self.gender = "M"
			elif value in utils[self.lang].KEYWORDS["female"]:
				self.gender = "F"
			else:
				self.d.log_message(f"Error: invalid gender - {value}")

		# look for keywords in categories
		if not self.gender and self.prefix != "person:fictional":
			for c in self.categories:
				if re.search("|".join(utils[self.lang].KEYWORDS["female"]), c.lower()):
					self.gender = "F"
				if re.search("|".join(utils[self.lang].KEYWORDS["male"]), c.lower()):
					self.gender = "M"
	
	##
	# @brief extracts and assigns jobs from the infobox
	def assign_jobs(self):
		data = self.get_infobox_data(utils[self.lang].KEYWORDS["jobs"])
		if data:
			jobs = []

			# [[...|data]]
			value = re.sub(r"\[\[[^]]*?\|(.+?)\]\]", r"\1", data)
			# [[data]]
			value = re.sub(r"\[\[(.+?)\]\]", r"\1", value)
			# {{nowrap|data}}
			value = re.sub(r"{{nowrap\|([^}]+)}}", r"\1", value, flags=re.I)

			# data (irrelevant data)
			value = re.sub(r"\(.*?\)", "", value).strip()
			# getting rid of wikipedia templates
			value = re.sub(r"\'{2,3}", "", value)
			value = re.sub(r"&nbsp;", " ", value)

			value = value.replace("\n", "").strip()
			# plainlists and flatlists - {{plainlist|*job *job}}
			pattern = r"\{\{(?:(?:indented\s)?plainlist|flatlist)\s*?\|(.*?)\}\}"
			match = re.search(pattern, value, flags=re.I)
			if match:
				array = match.group(1).strip()
				array = [a.strip() for a in array.split("*") if a]
				if len(array):
					jobs += array
					value = re.sub(pattern, "", value, flags=re.I).strip()
			
			# hlists and unbulleted lists - {{hlist|job|job}}
			pattern = r"\{\{(?:hlist|ubl|unbulleted\slist)\s*?\|(.*?)\}\}"
			match = re.search(pattern, value, flags=re.I)
			if match:
				array = match.group(1).strip()
				array = [a.strip() for a in array.split("|") if a]
				if len(array):
					jobs += array
					value = re.sub(pattern, "", value, flags=re.I).strip()

			# data {{unsuported template}}
			value = re.sub(r"\{\{.*?\}\}", "", value).strip()

			match = re.search(r"([;*•])", value)
			if match:
				char = match.group(1)
				array = value.split(char)
				array = [a.strip() for a in array if a]
				jobs += array
			elif value:
				value = value.replace(", and", ",")
				array = value.split(",")
				array = [a.strip() for a in array if a]
				jobs += array

			self.jobs = "|".join(jobs)
	
	##
	# @brief extracts nationality
	def assign_nationality(self):
		nationalities = []

		data = self.get_infobox_data(utils[self.lang].KEYWORDS["nationality"])
		if data:
			# remove irrelevant wiki templates
			value = re.sub(r"\{\{(?:citation|flagicon)[^}]*?\}\}", "", data, flags=re.I)
			value = re.sub(r"\[\[(?:image|file|soubor|obrázek):[^]]*?\]\]", "", value, flags=re.I)

			# [[...|data]]
			value = re.sub(r"\[\[[^]]*?\|(.+?)\]\]", r"\1", value)
			# [[data]]
			value = re.sub(r"\[\[(.+?)\]\]", r"\1", value)
			value = re.sub(r"\[|\]", "", value)
			# data (irrelevant data)
			value = re.sub(r"\(.*?\)", "", value).strip()
			
			# use other templates (e.g.: {{flag|...}}, {{USA}})
			value = re.sub(r"\{\{.+?\|(.+?)\}\}", r"\1", value)
			value = re.sub(r"\{\{(.*?)\}\}", r"\1", value)

			value = value.strip()

			value = re.sub(r"\s(?:and|a)\s", ",", value)
			value = re.sub(r"\s{2,}", ",", value)
			match = re.search(r"(/|-|–|,)", value) 
			if match:
				char = match.group(1)
				array = value.split(char)
				array = [a.strip() for a in array if a]
				nationalities += array
			else:
				nationalities.append(value)
			
			self.nationality = "|".join(nationalities)

	##
	# TODO: extract gender from categories
	def extract_text(self):
		# dates and places
		if self.birth_date or self.death_date or self.birth_place or self.death_place:
			birth_date, death_date, birth_place, death_place = utils[self.lang].extract_dates_and_places(self)
			if not self.birth_date:
				self.birth_date = birth_date
			if not self.death_date:
				self.death_date = death_date
			if not self.birth_place:
				self.birth_place = birth_place
			if not self.death_place:
				self.death_place = death_place

	##
	# @brief extracts and assigns art forms from the infobox
	#
	# NOT UNIFIED - cs version is not extracting artist entities yet
	def assign_art_forms(self):
		keys = ("movement", "field")

		art_forms = ""

		for key in keys:
			if key in self.infobox_data and self.infobox_data[key] != "":
				value = self.infobox_data[key].replace("\n", " ")
				if "''" in value:
					continue
				value = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", value)
				value = re.sub(r"\[|\]", "", value)
				value = re.sub(r"\{\{.*?\}\}", "", value)
				value = value.lower()
			  
				value = [item.strip() for item in value.split(",")]
				
				if len(value) == 1:
					value = value[0]
					value = [item.strip() for item in value.split("/")]
				
				value = "|".join(value)

				if value != "":
					if art_forms == "":
						art_forms = value
					else:
						art_forms += f"|{value}"
		
		self.art_forms = art_forms

	##
	# @brief extracts and assigns urls from the infobox
	#
	# NOT UNIFIED - cs version is not extracting artist entities yet
	def assign_urls(self):	
		urls = ""	
		if "website" in self.infobox_data and self.infobox_data["website"] != "":
			value = self.infobox_data["website"]
			value = re.sub(r"\{\{url\|(?:.*?=)?([^\|\}]+).*?\}\}", r"\1", value, flags=re.I)
			value = re.sub(r"\[(.*?)\s.*?\]", r"\1", value)
			urls = value
		self.urls = urls
