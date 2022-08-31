
import re
import mwparserfromhell as parser

class CoreUtils:

	DISAMBIG_PATTERN = r"{{[^}]*?(?:disambiguation|disambig|dab)(?:\|[^}]*?)?}}"
	CATEGORY_PATTERN = r"\[\[Category:\s?(.*?)\]\]"

	##
	# @brief determines if page is an entity or not
	#  
	# filters out wikipedia special pages and date pages
	def is_entity(title):
		# special pages
		if title.startswith(
			(
				"wikipedia:",
				"file",
				"mediawiki:",
				"template:",
				"help:",
				"category:",
				"special:",
				"portal:",
				"module:",
				"draft:",
				"user:",
				"list of",
				"geography of",
				"history of",
				"economy of",
				"politics of",
				"culture of",
				"bibliography of",
				"outline of",
				"music of",
				"flag of",
				"index of",
				"timeline of"
			)
		):
			return False

		if re.search(r"(?:january|february|march|april|may|june|july|august|september|october|november|december)(?:\s[0-9]+)?", title, re.I):
			return False

		return True

	##
	# @brief extracts the latitude and longtitude from a wikipedia formated string
	# @param format - wikipedia formated string
	# @return latitude, longtitude
	# 
	# e.g.: {{Coord|59|56|N|10|41|E|type:city}}
	@staticmethod
	def get_coordinates(format, debugger):
		# matching coords format with directions
		# {{Coord|59|56|N|10|41|E|type:city}}
		format = re.sub(r"\s", "", format)
		pattern = r"([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(N|S)\|([0-9.]+)\|([0-9.]+)?\|?([0-9.]+)?\|?(E|W)"
		m = re.search(pattern, format)
		if m:
			data = [x for x in m.groups() if x != None]
			data = [data[:int(len(data)/2)], data[int(len(data)/2):]]
			
			coords = [0, 0]
			
			# conversion calculation
			for d in range(2):
				for i in range(len(data[d])-1):
					coords[d] += float(data[d][i]) / 60*i if i != 0 else float(data[d][i])
				coords[d] = round(coords[d], 5)
				if data[d][-1] in ("S", "W"):
					coords[d] *= -1
				
			#print(f"latitude: {coords[0]}\nlongtitude: {coords[1]}\n")
			return (str(coords[0]), str(coords[1]))
		
		# matching coords format without directions (direct latitude and longtitude)
		# {{coord|41.23250|-80.46056|region:US-PA|display=inline,title}}
		pattern = r"{{.*\|([0-9.-]+)\|([0-9.-]+).*}}"
		m = re.search(pattern, format)
		if m:
			#print(f"latitude: {m.group(1)}\nlongtitude: {m.group(2)}\n")
			return (m.group(1), m.group(2))
		
		if re.search(r"[Cc]oords?missing", format):
			return (None, None)

		debugger.log_message(f"coords format no match ({format})")
		return (None, None)

	##
    # @brief extracts and assigns latitude and longitude from infobox
	#
	# general method for country, settlement, waterarea, watercourse and geo entities
	@staticmethod
	def assign_coordinates(infobox_data, debugger):

		latitude = ""
		longitude = ""

		if "coordinates" in infobox_data and infobox_data["coordinates"]:
			coords = CoreUtils.get_coordinates(infobox_data["coordinates"], debugger)
			if all(coords):
				latitude, longitude = coords
		
		return (latitude, longitude)

	##
    # @brief extracts and assigns area from infobox
	@classmethod
	def assign_area(cls, infobox_data, debugger):

		def fix_area(value):
			value = value.replace(",", "").strip()
			value = re.sub(r"\{\{.+\}\}", "", value)
			return value

		# km2
		keys = ("area_km2", "area_total_km2")
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				area = fix_area(value)
				if area:
					return area 

		# sq_mi
		keys = ("area_sq_mi", "area_total_sq_mi")
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				area = fix_area(value)
				area = cls.convert_units(area, "sqmi", debugger)
				if area:
					return area

		keys = ("area", "basin_size")
		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				# look for convert template - {{convert|...}}
				match = re.search(r"\{\{(?:convert|cvt)\|([^\}]+)\}\}", value, re.I)
				if match:
					area = match.group(1)
					area = area.split("|")
					if len(area) >= 2:
						number, unit = (area[0].strip(), area[1].strip())
						number = fix_area(number)
						number = cls.convert_units(number, unit, debugger)
						return number if number else ""

				# e.g.: '20sqmi', '10 km2', ...
				area = re.sub(r"\(.+\)", "", value).strip()
				match = re.search(r"^([\d,\.]+)(.*)", area, re.I)
				if match:
					number, unit = (match.group(1), match.group(2).strip())
					number = fix_area(number)
					number = cls.convert_units(number, unit, debugger)
					return number if number else ""

		# debugger.log_message(f"Error: unidentified area")
		return ""

	##
	# @brief converts units to metric system
	# @param number - number to be converted <string>
	# @param unit - unit abbreviation
	# @param round_to - to how many decimal points will be rounded to (default: 2)
	# @return converted rounded number as a string
	@staticmethod
	def convert_units(number, unit, debugger, round_to=2):
		try:
			number = float(number)
		except:
			debugger.log_message(f"couldn't conver string to float: {number}")
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
			debugger.log_message(f"Error: unit conversion error ({unit})")
			return ""

		return str(number if number % 1 != 0 else int(number))

	##
	# @brief tries to conver a string to a date with YYYY-MM-DD
	# @param data - string containing a date to be converted
	# @return array with 2 ordered dates
	# 
	# e.g.: example of return values: ["", ""], ["1952-07-23", ""], ["1952-07-23", "1999-04-27"]
	#
	# if the date is BC a minus sign is added before the year <br>
	# unknown values are substituted with question marks - e.g.: 1952-??-?? is a valid date (only the year was extracted) <br>
	# fictional dates are not accounted for <br>
	@staticmethod
	def extract_date(data):
		wikicode = parser.parse(data)
		templates = wikicode.filter_templates()
		
		if len(templates) > 0:
			new_templates = []
			for t in templates:
				if re.search(r"date|death|birth|dda|d-da|b-da", str(t), re.I) and not re.search(r"citation|note", str(t.name), re.I):
					new_templates.append(t)

			templates = new_templates

			if len(templates) == 0:
				string = wikicode.strip_code()
				templates = wikicode.filter_templates()
				for t in templates:
					params = t.params
					for p in params:
						string += f" {str(p.value)}"
				return [CoreUtils.parse_no_template(string.strip()), ""]

			template = templates[-1]

			if "based on age" in str(template).lower():
				# invalid template
				# TODO: log?
				return ["", ""]
			
			params = template.params
			date = []

			# filter empty fields, mf and df
			for p in params:
				param = p.value.strip()			
				if param != "" and not param.startswith("mf=") and not param.startswith("df=") and re.search(r".*?[0-9].*?", param):
					date.append(param)

			return CoreUtils.order_dates(CoreUtils.get_date(date, str(template.name)))            
		

		return [CoreUtils.parse_no_template(data), ""]

	##
	# @brief splits the date into 2 depending on the wikipedia format
	# @param date - array of date values (year, month, day)
	# @param name - wikipedia format name
	# @return array with 2 values (value is either a date or left empty)
	#
	# date extraction helper function
	@staticmethod
	def get_date(date, name):
		result = []

		if len(date) > 3 or re.search(r".*?(?:death(?:-| )(?:date|year) and age|dda|d-da).*?", name, re.I):
			# split dates
			if len(date) % 2 != 0:
				return ["", ""]
			result.append(CoreUtils.parse_date(date[:int(len(date)/2)]))
			result.append(CoreUtils.parse_date(date[int(len(date)/2):]))
		else:
			result.append(CoreUtils.parse_date(date))
			result.append("")

		return result

	##
	# @brief determines the date format and calls the appropriate function
	# @param date - array of date values
	# @return date in YYYY-MM-DD format
	#
	# date extraction helper function
	@staticmethod
	def parse_date(date):
		if len(date) < 1:
			return ""
		
		for item in date:
			if not item.isnumeric():
				return CoreUtils.parse_string_format(item)
		return CoreUtils.parse_num_format(date)

	##
	# @brief deals with the numerical date format
	# @param array - array of date values
	# @return date in YYYY-MM-DD format
	# 
	# e.g: {{Birth date|1962|1|16}}
	#
	# date extraction helper function
	@staticmethod
	def parse_num_format(array):
		# e.g.: ['1919', '5'] -> 1919-05-??
		if len(array) > 3:
			# TODO: log invalid
			return ""

		while len(array) < 3:
			array.append("??")

		for i in range(len(array)):
			if array[i].isnumeric():
				if int(array[i]) < 10 and len(array[i]) == 1:
					array[i] = f"0{array[i]}"
		
		return "-".join(array)
	
	##
	# @brief deals with the string date format
	# @param string - date
	# @return date in YYYY-MM-DD format
	# 
	# e.g.: {{Birth date|January 16, 1962}}
	#
	# date extraction helper function
	@staticmethod
	def parse_string_format(string):     
		months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

		date = []

		# month first
		match = re.search(r"^([a-z]+)[^0-9a-z]+?([0-9]+)[^0-9a-z]+?(-?[0-9]+)", string, re.I)
		if match:
			groups = list(match.groups())
			if groups[0].lower() in months:			
				groups[0] = str(months.index(groups[0].lower())+1)
				for i in range(len(groups)):
					if groups[i].isnumeric():
						if 0 < int(groups[i]) < 10 and len(groups[i]) == 1:
							groups[i] = f"0{groups[i]}"
				date.append(groups[2])
				date.append(groups[0])
				date.append(groups[1])
				return "-".join(date)

		# day first
		match = re.search(r"^([0-9]+)[^\(\)0-9]+?([a-z]+)[^\(\)]+?(-?[0-9]+)", string, re.I)
		if match:
			groups = list(match.groups())
			if groups[1].lower() in months:	
				groups[1] = str(months.index(groups[1].lower())+1)
				for i in range(len(groups)):
					if groups[i].isnumeric():
						if 0 < int(groups[i]) < 10 and len(groups[i]) == 1:
							groups[i] = f"0{groups[i]}"
				date.append(groups[2])
				date.append(groups[1])
				date.append(groups[0])
				return "-".join(date)

		# month and year
		match = re.search(r"^([a-z]+).+?(-?[0-9]+)(?:\s|$)", string, re.I)
		if match:
			groups = list(match.groups())
			if groups[0].lower() in months:	
				groups[0] = str(months.index(groups[0].lower())+1)
				if 0 < int(groups[0]) < 10 and len(groups[0]) == 1:
					groups[0] = f"0{groups[0]}"
				date.append(groups[1])
				date.append(groups[0])
				date.append("??")
				return "-".join(date)

		# year only
		match = re.search(r"^(-?[0-9]+)(?:[^,0-9]|$)", string, re.I)
		if match:
			date.append(match.group(1))
			date.append("??")
			date.append("??")
			return "-".join(date)

		# invalid date
		# TODO: log?
		return ""

	##
	# @brief deals dates when no template was found
	# @param string - date with no template
	# @return date in YYYY-MM-DD format
	# 
	# e.g.: January 16, 1962 (extracted from the first sentence)
	#
	# date extraction helper function
	@staticmethod
	def parse_no_template(string):
		if re.search(r"[0-9]+/[0-9]+/[0-9]+", string):
			# invalid template
			# TODO: log?
			return ""

		string = re.sub(r"''circa''|circa|c\.|\(.*?age.*?\)|no|AD", "", string, re.I)
		string = re.sub(r"{{nbsp}}|&nbsp;", " ", string, re.I)
		string = re.sub(r"([0-9]+)(?:\/|–|-)[0-9]+", r"\1", string, re.I)
		string = re.sub(r"([0-9]+)\s+BCE?|BCE?\s+([0-9]+)", r"-\1\2", string, re.I)

		return CoreUtils.parse_string_format(string.strip())

	##
	# @brief orders dates (from oldest to newest)
	# @param array - array with up to 2 dates
	# @return ordered array of dates
	#
	# date extraction helper function
	@staticmethod
	def order_dates(array):
		reverse = True if array[0].startswith("-") and array[1].startswith("-") else False
		return sorted(array, key=lambda x: x if x != "" else "z", reverse=reverse)
