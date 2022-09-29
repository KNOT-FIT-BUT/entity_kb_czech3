##
# @file person_utils.py
# @brief en specific person utilities
# @author created by Jan Kapsa (xkapsa00)
# @date 29.09.2022

import re
from debugger import Debugger as debug
from lang_modules.en.core_utils import CoreUtils

class PersonUtils:
	##
	# @brief assigns prefix based on entity categories or infobox names
	#
	# person, person:fictional, person:artist or person:group
	@staticmethod
	def assign_prefix(person):
		if re.search(r".*\s(?:,|and|&)\s.*", person.title):
			return "person:group"

		# self.d.log_message(self.first_sentence)

		if "character" in person.infobox_name or "fictional" in person.description:
			return "person:fictional"

		for c in person.categories:
			if "fictional" in c.lower():
				return "person:fictional"

		if person.infobox_name.lower() == "artist":
			return "person:artist"

		# artist, painter, writer

		for c in person.categories:
			if re.search(r"artist", c, re.I):				
				return "person:artist"

		return "person"

	##
	# @brief extracts and assigns dates from infobox or from the first sentence
	@staticmethod
	def assign_dates(person):
		birth_date = ""
		death_date = ""

		if "birth_date" in person.infobox_data and person.infobox_data["birth_date"] != "":
			date = person.infobox_data["birth_date"].strip()
			extracted = CoreUtils.extract_date(date)
			birth_date = extracted[0]
		
		if "death_date" in person.infobox_data and person.infobox_data["death_date"] != "":
			date = person.infobox_data["death_date"].strip()
			extracted = CoreUtils.extract_date(date)
			if extracted[1] == "":
				death_date = extracted[0]
			else:
				if birth_date == "":
					birth_date = extracted[0]
				death_date = extracted[1]
		
		# debugger.log_message((birth_date, death_date))
		return (birth_date, death_date)

	def extract_dates_and_places(person):
		birth_date = ""
		death_date = ""
		birth_place = ""
		death_place = ""
		sentence = person.first_sentence
		
		match = re.search(r"\((.*?)\)", sentence)
		if match:
			group = match.group(1)
			group = re.sub(r"\[\[.*?\]\]", "", group)
			group = re.sub(r"\{\{.*?\}\};?", "", group)
			group = re.sub(r"&ndash;|{{spaced ndash}}|{{snd}}|{{ndash}}|{{spaced en dash}}|{{snds}}|{{spnd}}", "–", group).strip()
			group = re.sub(r"{{Spaces}}|{{nbsp}}", " ", group)
			group = group.split("–")
			if len(group) == 2:
				# get rid of born and died
				born = group[0].replace("born", "").strip()
				died = group[1].replace("died", "").strip()
				if "BC" in died and "BC" not in born:
					born += " BC"
				birth_date = CoreUtils.extract_date(born)[0]
				death_date = CoreUtils.extract_date(died)[0]
			else:
				date = group[0]
				# look for born and died
				if "born" in date:
					date = date.replace("born", "").strip()
					birth_date = CoreUtils.extract_date(date)[0]
				elif "died" in date:
					date = date.replace("died", "").strip()
					death_date = CoreUtils.extract_date(date)[0]
				else:
					birth_date = CoreUtils.extract_date(date)[0]

			if len(group) == 2:
				match = re.search(r"\s+in\s+(.*)", group[0])
				if match:
					birth_place = match.group(1).strip()
				match = re.search(r"\s+in\s+(.*)", group[1])
				if match:					
					death_place = match.group(1).strip()
			else:
				group = group[0]
				match = re.search(r".*?born.*?\s+in\s+([^\d]+)", group)
				if match:
					birth_place = match.group(1).strip()
				match = re.search(r".*?died.*?\s+in\s+([^\d]+)", group)
				if match:					
					death_place = match.group(1).strip()

		return (birth_date, death_date, birth_place, death_place)
	
	##
	# @brief extracts data from the first paragraph and categories
	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		
		birth_date, death_date, prefix = (
			extracted["birth_date"],
			extracted["death_date"],
			extracted["prefix"]
		)

		first_paragraph, categories = (
			ent_data["first_paragraph"],
			ent_data["categories"]
		)		

		# try to get the date from the 1st sentence
		if (death_date == "" or birth_date == "") and prefix != "person:fictional":
			match = re.search(r"\((.*?)\)", first_paragraph)
			if match:
				group = match.group(1)
				group = re.sub(r"\[\[.*?\]\]", "", group)
				group = re.sub(r"\{\{.*?\}\};?", "", group)
				group = re.sub(r"&ndash;", "–", group).strip()
				group = group.split("–")
				if len(group) == 2:
					# get rid of born and died
					born = group[0].replace("born", "").strip()
					died = group[1].replace("died", "").strip()
					if "BC" in died and "BC" not in born:
						born += " BC"
					extracted["birth_date"] = CoreUtils.extract_date(born)[0]
					extracted["death_date"] = CoreUtils.extract_date(died)[0]
				else:
					date = group[0]
					# look for born and died
					if "born" in date:
						date = date.replace("born", "").strip()
						extracted["birth_date"] = CoreUtils.extract_date(date)[0]
					elif "died" in date:
						date = date.replace("died", "").strip()
						extracted["death_date"] = CoreUtils.extract_date(date)[0]
					else:
						extracted["birth_date"] = CoreUtils.extract_date(date)[0]

		# extracting gender from categories
		# e.g.: two and a half men -> can't extract gender from this
		if not extracted["gender"]:
			if prefix != "person:fictional":
				for c in categories:
					if "women" in c.lower() or "female" in c.lower():
						extracted["gender"] = "F"
						return extracted
					if "male" in c.lower():
						extracted["gender"] = "M"
						return extracted

		# gender: if there is he/his/she/her in the second sentence
		if not extracted["gender"]:
			# TODO: split lines better
			paragraph_split = first_paragraph.split(".")
			if len(paragraph_split) > 1:
				#print(f"{self.title}: {paragraph_split[1].strip()}")
				match = re.search(r"\b[Hh]e\b|\b[Hh]is\b", paragraph_split[1].strip())
				if match:
					extracted["gender"] = "M"
					return extracted
				match = re.search(r"\b[Ss]he\b|\b[Hh]er\b", paragraph_split[1].strip())
				if match:
				# else:
				#     print(f"{self.title}: undefined")
					extracted["gender"] = "F"

		return extracted

