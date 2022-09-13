##
# @file ent_core.py
# @brief contains EntCore entity - parent core enitity with useful functions
# 
# see class for more information
#
# @section important_functions important functions
# - image and alias extraction
# - date extraction
# - unit conversion
# - latitude and longtitude extraction
#
# @section general_ent_information general entity information
# - ID
# - prefix
# - title
# - aliases
# - redirects
# - description
# - original title
# - images
# - link
#
# description is first sentence extracted from a file passed to the core entity during initialization <br>
# if first sentece is not found in the file it is extracted with the get_first_sentence function <br>
# but first sentece with wikipedia formatting is also stored because it helps with extraction of other information
# 
# @section date_conversion date conversion 
# main function extracting dates is the extract_date function <br>
# other date functions are helper function to the main function and they are not ment to be called
#
# @author created by Jan Kapsa (xkapsa00)
# @date 28.07.2022

from abc import ABCMeta, abstractmethod
import re
from hashlib import md5, sha224
import mwparserfromhell as parser

from lang_modules.en.core_utils import CoreUtils as EnCoreUtils
from lang_modules.cs.core_utils import CoreUtils as CsCoreUtils

utils = {
	"en": EnCoreUtils,
	"cs": CsCoreUtils
}

## 
# @class EntCore
# @brief abstract parent entity
# 
# contains the general information that is shared across all entities and some useful functions
class EntCore(metaclass=ABCMeta):
	# FIXME: this is a bad idea because of multiprocessing 
	counter = 0

	##
	# @brief initializes the core entity
	# @param title - page title (entity name) <string>
	# @param prefix - entity type <string>
	# @param link - link to the wikipedia page <string>
	# @param data - extracted entity data (infobox data, categories, ...) <dictionary>
	# @param langmap - language abbreviations <dictionary>
	# @param redirects - redirects to the wikipedia page <array of strings>
	# @param sentence - first sentence of the page <string>
	# @param debugger - instance of the Debugger class used for debugging <Debugger>
	@abstractmethod
	def __init__(self, title, prefix, link, data, langmap, redirects, sentence, debugger):
		EntCore.counter += 1
		self.d = debugger

		# general information
		self.eid = sha224(str(EntCore.counter).encode("utf-8")).hexdigest()[:10]
		self.prefix = prefix
		self.title = re.sub(r"\s+\(.+?\)\s*$", "", title)
		self.aliases = ""
		self.redirects = redirects
		self.description = sentence
		self.original_title = title
		self.images = ""
		self.link = link
		self.langmap = langmap

		self.lang = link[8:10]
		self.core_utils = utils[self.lang]

		# extracted data
		self.infobox_data       = data["data"]
		self.infobox_name       = data["name"]
		self.categories         = data["categories"]
		self.first_paragraph    = data["paragraph"]
		self.coords             = data["coords"]
		self.extract_images     = data["images"]
		
		self.first_sentence = ""
		
		self.extract_image()
		self.get_first_sentence()

		if self.lang == "en":
			if self.first_paragraph:
				self.get_aliases()


	##
	# @brief serializes entity data for output (tsv format)
	# @param ent_data - child entity data that is merged with general data <tsv string>
	# @return tab separated values containing all of entity data <string>
	def serialize(self, ent_data):
		data = "\t".join([
			self.eid,
			self.prefix,
			self.title,
			self.aliases,
			"|".join(self.redirects),
			self.description,
			self.original_title,
			self.images,
			self.link,
			ent_data
		]).replace("\n", "")
		return data

	##
	# @brief extracts data from infobox dictionary given an array of keys
	# @return array of data found in the infobox dictionary
	def get_infobox_data(self, keys, return_first=True):
		if isinstance(keys, str):
			keys = [keys]
		data = []
		for key in keys:
			if key in self.infobox_data and self.infobox_data[key]:
				value = self.infobox_data[key]
				if return_first:
					return value
				else:
					data.append(self.infobox_data[key])

		return "" if return_first else data

	##
	# @brief removes wikipedia formatting
	# @param data - string with wikipedia formatting
	# @return string without wikipedia formatting
	@staticmethod
	def remove_templates(data):
		data = re.sub(r"\{\{.*?\}\}", "", data)
		data = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", data)
		data = re.sub(r"\[|\]|'|\(\)", "", data)
		return data

	##
	# @brief extracts and assigns area from infobox
	def assign_area(self):
		def fix_area(value):
			area = re.sub(r"&nbsp;", "", value)
			area = re.sub(r"(?<=\d)\s(?=\d)", "", area)
			area = re.sub(r"\{\{.*\}\}", "", area)
			area = re.sub(r",(?=\d{3})", "", area)
			area = area.replace(",", ".")
			area = re.sub(r"(\d+(?:\.\d+)?).+", r"\1", area)
			return area.strip()

		# km2
		data = self.get_infobox_data(utils[self.lang].KEYWORDS["area_km2"], return_first=False)
		for d in data:
			area = fix_area(d)
			if area:
				return area

		# sq_mi
		data = self.get_infobox_data(utils[self.lang].KEYWORDS["area_sqmi"], return_first=False)
		for d in data:
			area = fix_area(d)
			area = self.convert_units(area, "sqmi")
			if area:
				return area

		data = self.get_infobox_data(utils[self.lang].KEYWORDS["area_other"], return_first=False)
		for d in data:
			# look for convert template - {{convert|...}}
			match = re.search(r"\{\{(?:convert|cvt)\|([^\}]+)\}\}", d, re.I)
			if match:
				area = match.group(1)
				area = area.split("|")
				if len(area) >= 2:
					number, unit = (area[0].strip(), area[1].strip())
					number = fix_area(number)
					number = self.convert_units(number, unit)
					return number if number else ""

			# e.g.: '20sqmi', '10 km2', ...
			area = re.sub(r"\(.+\)", "", d).strip()
			match = re.search(r"^([\d,\.]+)(.*)", area, re.I)
			if match:
				number, unit = (match.group(1), match.group(2).strip())
				number = fix_area(number)
				number = self.convert_units(number, unit)
				return number if number else ""

		# debugger.log_message(f"Error: unidentified area")
		return ""

	##
	# @brief converts units to metric system
	# @param number - number to be converted <string>
	# @param unit - unit abbreviation
	# @param round_to - to how many decimal points will be rounded to (default: 2)
	# @return converted rounded number as a string
	def convert_units(self, number, unit, round_to=2):
		try:
			number = float(number)
		except:
			self.d.log_message(f"couldn't conver string to float: {number}")
			return ""
		unit = unit.lower()

		SQMI_TO_KM2 = 2.589988
		HA_TO_KM2 = 0.01
		ACRE_TO_KM2 = 0.00404685642
		M2_TO_KM2 = 0.000001
		MI2_TO_KM2 = 2.589988
		FT_TO_M = 3.2808
		MI_TO_KM = 1.609344
		CUFT_TO_M3 = 0.028317
		FT3_TO_M3 = 0.0283168466
		L_TO_M3 = 0.001

		accepted_untis = ["sqkm", "km2", "km²", "km", "m", "meters", "metres", "m3", "m3/s", "m³/s"]
		if unit in accepted_untis:
			return str(number if number % 1 != 0 else int(number))

		if unit == "sqmi":
			number = round(number * SQMI_TO_KM2, round_to)
		elif unit in ("mi", "mile", "miles"):
			number = round(number * MI_TO_KM,round_to)
		elif unit in ("ft", "feet"):
			number = round(number / FT_TO_M, round_to)
		elif unit in ("cuft/s", "cuft"):
			number = round(number * CUFT_TO_M3,round_to)
		elif unit == "ft3/s":
			number = round(number * FT3_TO_M3, round_to)
		elif unit == "l/s":
			number = round(number * L_TO_M3, round_to)
		elif unit == "ha":
			number = round(number * HA_TO_KM2, round_to)
		elif unit in ("acres", "acre"):
			number = round(number * ACRE_TO_KM2, round_to)
		elif unit == "m2":
			number = round(number * M2_TO_KM2, round_to)
		elif unit == "mi2":
			number = round(number * MI2_TO_KM2, round_to)
		else:
			self.d.log_message(f"Error: unit conversion error ({unit})")
			return ""

		return str(number if number % 1 != 0 else int(number))

	##
	# @brief extracts image data from the infobox
	def extract_image(self):
		if len(self.extract_images):
			extracted_images = [img.strip().replace(" ", "_") for img in self.extract_images]
			extracted_images = [self.get_image_path(img) for img in extracted_images]
			self.images = "|".join(extracted_images)

		data = self.get_infobox_data(utils[self.lang].KEYWORDS["image"], return_first=False)
		for d in data:
			image = d.replace("\n", "")
			if not image.startswith("http"):
				image = self.get_images(image)
				self.images += image if not self.images else f"|{image}"

	##
	# @brief removes wikipedia formatting and assigns image paths to the images variable
	# @param image - image data with wikipedia formatting
	def get_images(self, image):
		result = []

		image = re.sub(r"file:", "", image, flags=re.I)
		
		images = []
		
		if re.search(r"\{|\}", image):
			wikicode = parser.parse(image)
			templates = wikicode.filter_templates(wikicode)
			for t in templates:
				params = t.params
				for p in params:
					if re.search(r"image|photo|[0-9]+", str(p.name), re.I):
						if re.search(r"\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)", str(p.value), re.I):
							images.append(str(p.value))

		if not len(images):
			images.append(image)
		
		images = [re.sub(r"^(?:\[\[(?:image:)?)?(.*?(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)).*$", r"\1", img, flags=re.I) for img in images]
		images = [img.strip().replace(" ", "_") for img in images]

		result = [self.get_image_path(img) for img in images]

		return "|".join(result)

	##
	# @brief generates server path from an image name
	# @param image - image name 
	@staticmethod
	def get_image_path(image):
		image_hash = md5(image.encode("utf-8")).hexdigest()[:2]
		image_path = f"wikimedia/commons/{image_hash[0]}/{image_hash}/{image}"
		return image_path

	# get_aliases
	# get_description

	##
	# @brief tries to extract the first sentence from the first paragraph
	# @param paragraph - first paragraph of the page <string>
	#
	# removes the wikipedia formatting and assigns the description variable if it is empty
	# but first sentece with wikipedia formatting is also stored because it helps with extraction of other information
	#
	# e.g.: '''Vasily Vasilyevich Smyslov''' (24 March 1921 – 27 March 2010) was a [[Soviet people|Soviet]] ...
	def get_first_sentence(self):
		paragraph = self.first_paragraph.strip()
		if paragraph and paragraph[-1] != '.':
			paragraph += '.'

		# TODO: make this better -> e.g.: Boleslav Bárta - ... 90. let ...
		keywords = self.core_utils.KEYWORDS["sentence"]
		pattern = r"('''.*?'''.*?(?: (?:" + f"{'|'.join(keywords)}" + r") ).*?(?<!\s[A-Z][a-z])(?<!\s[A-Z])\.)"		
		match = re.search(pattern, paragraph)
		if match:
			sentence = match.group(1)
			sentence = re.sub(r"&nbsp;", " ", sentence)
			sentence = re.sub(r"\[\[([^\|]*?)\]\]", r"\1", sentence)
			sentence = re.sub(r"\[\[.*?\|([^\|]*?)\]\]", r"\1", sentence)
			sentence = re.sub(r"\[|\]", "", sentence)
			# self.d.log_message(sentence)
			self.first_sentence = sentence

	##
	# @brief extracts an alias in a native language
	# @param langs - aliases in a wikipedia format <array of strings>
	# 
	# e.g.: {{lang-rus|Васи́лий Васи́льевич Смысло́в|Vasíliy Vasíl'yevich Smyslóv}};
	def get_lang_aliases(self, langs):
		if len(langs) > 0:
			for lang in langs:
				lang = re.sub(r"{{lang(?:-|\|)(.*?)}}", r"\1", lang)
				split = lang.split("|")
				code = split[0].split("-")[0]
				if len(code) != 2:
					if code in self.langmap:
						code = self.langmap[code].split("|")[0]
					else:
						code = "??"
				
				for s in split[1:]:
					if "=" in s:
						split.remove(s)

				if len(split) < 2:
					# self.d.log_message(f"couldn't split lang alias: {split[0]} [{self.link}]")
					return

				alias = split[1]
				if len(split) > 2:
					if "{" not in alias:
						if self.aliases:
							self.aliases += f"|{alias}#lang={code}"
						else:
							self.aliases = f"{alias}#lang={code}"

	##
	# @brief extracts aliases from the first sentence
	def get_aliases(self):
		title = self.title
		sentence = self.first_sentence

		sentence = re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", sentence)
		sentence = re.sub(r"\[|\]", "", sentence)
		
		aliases = []
	
		split = title.split(" ")
		name = split[0]
		surname = split[-1] if len(split) > 1 else ""
		
		# finds all names in triple quotes and removes those that match the title 
		aliases = re.findall(r"(?:\"|\()?'''.*?'''(?:\"|\))?", sentence)
		aliases = [re.sub(r"'{3,5}", "", a) for a in aliases]
		aliases = [a for a in aliases if a != title]
		
		title_data = title.split(" ")
		
		# handles born surnames (née)
		born_name = ""
		m = re.search(r".*née\s'''(.*?)'''.*", sentence)
		if m:
			born_name = m.group(1)
		
		# handles aliases in double quotes and brackets
		# surname is added to nicknames as a rule
		patterns = [r"\"(.*?)\"", r"\((.*?)\)"]
		nicknames = []
		for pattern in patterns:
			for i in range(len(aliases)):
				m = re.search(pattern, aliases[i])
				if m:
					if m.start():
						cut = f"{aliases[i][:m.start()].strip()} {aliases[i][m.end():].strip()}"
						aliases[i] = cut
					else:
						if i-1 >= 0 and i+1 < len(aliases):
							cut = f"{aliases[i-1]} {aliases[i+1]}"
							aliases[i-1] = cut
							aliases[i+1] = ""
					nicknames.append(m.group(1))
		
		nicknames = [
			f"{nick} {surname}" for nick in nicknames 
			if f"{nick} {surname}" != title 
			and nick != title
		]
		
		# remove previously handeled nicknames and born surname
		aliases = [
			item for item in aliases 
			if item 
			and item not in title_data 
			and '"' not in item
			and "(" not in item
			and item != title
		]
		if born_name and born_name != title:
			aliases = [item for item in aliases if item != born_name]
		
		aliases = [re.sub(r"\(|\)", "", a).strip() for a in aliases]

		aliases += nicknames
		if born_name and born_name != title:
			aliases.append(f"{name} {born_name}")
		
		self.aliases = self.aliases.split("|")
		self.aliases += aliases
		
		# TODO: get aliases from infoboxes
		# keys = ["name", "birth_name", "birthname", "native_name", "nativename", "aliases"]
		# for key in keys:
		#     if key in self.infobox_data and self.infobox_data[key]:
		#         value = self.infobox_data[key]
		#         if value != title and value not in self.aliases:
		#             self.d.log_message(f"{key} -> {value}")

		self.aliases = [re.sub(r"\{\{.*?\}\}", "", a).strip() for a in self.aliases]
		self.aliases = [a for a in self.aliases if a != title]
		self.aliases = [a for a in self.aliases if a != ""]

		self.aliases = "|".join(self.aliases)

		# if self.aliases:
		#     self.d.log_message(f"{'|'.join(self.aliases)}")
		pass    
	