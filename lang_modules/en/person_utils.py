
import re

from lang_modules.en.core_utils import CoreUtils

class PersonUtils:

	@staticmethod
	def extract_infobox(ent_data, debugger):
		
		extraction = {
			"aliases": "",
			"prefix": "",
			"birth_date": "",
			"death_date": "",
			"birth_place": "",
			"death_place": "",
			"gender": "",
			"jobs": "",
			"nationality": "",
			
			# artist data
			"art_forms": "",
			"urls": ""
		}

		title, sentence, infobox_data, infobox_name, categories = (
			ent_data["title"], 
			ent_data["sentence"], 
			ent_data["infobox_data"],
			ent_data["infobox_name"], 
			ent_data["categories"]
		)

		extraction["prefix"] = PersonUtils.assign_prefix(title, sentence, infobox_name, categories)
		
		extraction["birth_date"], extraction["death_date"] = PersonUtils.assign_dates(infobox_data, debugger)
		extraction["birth_place"], extraction["death_place"] = PersonUtils.assign_places(infobox_data, debugger)
		extraction["nationality"] = PersonUtils.assign_nationality(infobox_data, debugger)
		extraction["gender"] = PersonUtils.assign_gender(infobox_data)
		extraction["jobs"] = PersonUtils.assign_jobs(infobox_data)        

		if extraction["prefix"] == "person:artist":
			extraction["art_froms"] = PersonUtils.assign_art_forms(infobox_data)
			extraction["urls"] = PersonUtils.assign_urls(infobox_data)

		return extraction

	##
	# @brief assigns prefix based on entity categories or infobox names
	#
	# person, person:fictional, person:artist or person:group
	@staticmethod
	def assign_prefix(title, sentence, infobox_name, categories):
		
		# self.d.log_message(self.title)

		if re.search(r".*\s(?:,|and|&)\s.*", title):
			return "person:group"

		# self.d.log_message(self.first_sentence)

		if "character" in infobox_name or "fictional" in sentence:
			return "person:fictional"

		for c in categories:
			if "fictional" in c.lower():
				return "person:fictional"

		if infobox_name.lower() == "artist":
			return "person:artist"

		# artist, painter, writer

		for c in categories:
			if re.search(r"artist", c, re.I):				
				return "person:artist"

		return "person"

	##
	# @brief extracts and assigns dates from infobox or from the first sentence
	@staticmethod
	def assign_dates(infobox_data, debugger):
		
		birth_date = ""
		death_date = ""
		
		if "birth_date" in infobox_data and infobox_data["birth_date"] != "":
			date = infobox_data["birth_date"].strip()
			extracted = CoreUtils.extract_date(date)
			birth_date = extracted[0]
		
		if "death_date" in infobox_data and infobox_data["death_date"] != "":
			date = infobox_data["death_date"].strip()
			extracted = CoreUtils.extract_date(date)
			if extracted[1] == "":
				death_date = extracted[0]
			else:
				if birth_date == "":
					birth_date = extracted[0]
				death_date = extracted[1]
		
		# debugger.log_message((birth_date, death_date))
		return (birth_date, death_date)

	##
	# @brief extracts and assigns places from infobox, removes wikipedia formatting
	@staticmethod
	def assign_places(infobox_data, debugger):

		birth_place = ""
		death_place = ""

		if "birth_place" in infobox_data:
			birth_place = PersonUtils.fix_place(infobox_data["birth_place"])

		if "death_place" in infobox_data:
			death_place = PersonUtils.fix_place(infobox_data["death_place"])

		# debugger.log_message((birth_place, death_place))
		return (birth_place, death_place)

	##
	# @brief removes wikiepdia formatting from places
	# @param place - wikipedia formatted string
	# @return string result without formatting
	@staticmethod
	def fix_place(place):
		p = place

		if p:
			p = re.sub(r"{{nowrap\|(.*?)}}", r"\1", p)
			p = re.sub(r"\{\{.*?\}\}", "", p)
			p = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", p)
			p = re.sub(r"\[|\]", "", p)
			return p.strip()

		return ""

	##
	# @brief extracts and assigns nationality from infobox, removes wikipedia formatting
	@staticmethod
	def assign_nationality(infobox_data, debugger):
		if "nationality" in infobox_data and infobox_data["nationality"] != "":
			nationalities = []
			string = infobox_data["nationality"]

			if string:
				# removing stuff in () and [] brackets 
				# (e.g.: [[Belgium|Belgian]] (1949—2003), [[Chile]]an[[Mexico|Mexican]])
				string = re.sub(r"\(.*\)|\[|\]", "", string).strip()
				
				# case splitting 
				# (e.g.: GermanAmerican)
				indexes = [m.start(0) for m in re.finditer(r"[a-z][A-Z]", string)]
				x = 0
				for i in indexes:
					nationalities.append(string[x:i+1])
					x = i+1
				nationalities.append(string[x:])
				
				# other splitting 
				# (e.g.: French-Moroccan)
				splitters = ["/", "-", "–", ","]
				for splitter in splitters:
					tmp = []
					for s in nationalities:
						for a in s.split(splitter):
							tmp.append(a)
					
					nationalities = tmp
				
				# splitting redirects 
				# (e.g.: [[Germans|German]]) -> German
				for i in range(len(nationalities)):
					bar_split = nationalities[i].split("|")
					bar_split[-1] = re.sub(r"{|}", "", bar_split[-1]).strip()
					nationalities[i] = bar_split[-1]
				
				return "|".join(nationalities)
		return ""

	##
	# @brief extracts and assigns gender from the infobox
	@staticmethod
	def assign_gender(infobox_data):
		if "gender" in infobox_data and infobox_data["gender"] != "":
			gender = infobox_data["gender"].lower()
			if gender == "male":
				return "M"
			elif gender == "female":
				return "F"		
			return gender
		
		return ""

	##
	# @brief extracts and assigns jobs from the infobox
	@staticmethod
	def assign_jobs(infobox_data):
		if "occupation" in infobox_data and infobox_data["occupation"] != "":
			string = infobox_data["occupation"]
			string = re.sub("\[|\]|\{|\}", "", string)
			occupation = [s.lower().strip() for s in string.split(",")]

			for i in range(len(occupation)):
				bar_split = occupation[i].split("|")
				occupation[i] = bar_split[-1]

			tmp = []
			for o in occupation:
				star_split = o.split("*")
				for s in star_split:
					if s != "":
						tmp.append(s.strip())
			
			occupation = [t for t in tmp if t]
			
			return "|".join(occupation).replace("\n", " ")
		return ""

	##
	# @brief extracts and assigns art forms from the infobox
	@staticmethod
	def assign_art_forms(infobox_data):
		
		keys = ["movement", "field"]

		art_forms = ""

		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				value = infobox_data[key].replace("\n", " ")
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
		
		return art_forms

	##
	# @brief extracts and assigns urls from the infobox
	@staticmethod
	def assign_urls(infobox_data):		
		if "website" in infobox_data and infobox_data["website"] != "":
			value = infobox_data["website"]

			value = re.sub(r"\{\{url\|(?:.*?=)?([^\|\}]+).*?\}\}", r"\1", value, flags=re.I)
			value = re.sub(r"\[(.*?)\s.*?\]", r"\1", value)

			return value
		return ""

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