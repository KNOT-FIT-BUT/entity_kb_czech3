
import re

from lang_modules.en.core_utils import CoreUtils

class EventUtils:

	@staticmethod
	def extract_infobox(ent_data, debugger):

		extraction = {
			"start_date": "",
			"end_date": "",
			"locations": "",
			"type": ""
		}

		infobox_data = ent_data["infobox_data"]

		extraction["start_date"], extraction["end_date"] = EventUtils.assign_dates(infobox_data)
		extraction["locations"] = EventUtils.assign_locations(infobox_data)
		extraction["type"] = EventUtils.assign_type(infobox_data)

		return extraction
	
	##
    # @brief extracts and assigns start date and end date variables from infobox
	@staticmethod
	def assign_dates(infobox_data):
		start_date = ""
		end_date = ""

		keys = ["year", "start_date", "first_aired", "election_date"]

		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = CoreUtils.extract_date(data)
				start_date = data[0]

		keys = ["end_date"]

		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = CoreUtils.extract_date(data)
				end_date = data[0]

		keys = ["date"]
		
		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				split = data.split("–")
				split = [item.strip() for item in split if item != ""]
				if len(split) == 1:
					date = CoreUtils.extract_date(split[0])
					start_date = date[0]
					end_date = date[1]						
					break
				else:
					
					# 19-25 September 2017 -> 19 September 2017 - 25 September 2017
					if re.search(r"^[0-9]+$", split[0]):
						match = re.search(r"^[0-9]+?\s+?([a-z]+?\s+?[0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return (start_date, end_date)

					# January-September 2017 -> January 2017 - September 2017
					if re.search(r"^[a-z]+$", split[0], re.I):
						match = re.search(r"^[a-z]+?\s+?([0-9]+)", split[1], re.I)
						if match:
							split[0] += f" {match.group(1)}"
						else:
							return (start_date, end_date)

					start_date = CoreUtils.extract_date(split[0])[0]
					end_date = CoreUtils.extract_date(split[1])[0]

		return (start_date, end_date)

	##
    # @brief extracts and assigns locations from infobox
	@staticmethod
	def assign_locations(infobox_data):
		locations = []
		
		keys = [
			"place", 
			"country",
			"location",
			"areas",
			"city",
			"host_city",
			"cities",
			"affected",
			"site",
			"venue"
		]

		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = EventUtils.remove_templates(data)
				
				if re.search(r"[a-z][A-Z]", data):
					string = re.sub(r"([a-z])([A-Z])", r"\1|\2", data)
					split = string.split("|")
					found = False
					for s in split:
						if "," not in s:
							found = True
							break
					if found:
						string = re.sub(r"([a-z])([A-Z])", r"\1, \2", data)
						locations.append(string)
					else:
						locations = split
					break
				
				if "," in data:
					split = data.split(",") 
					if len(split) > 5:
						locations = [item.strip() for item in split]
						break

				locations.append(data)
				break
		
		return locations 

	##
    # @brief extracts and assigns type from infobox
	@staticmethod
	def assign_type(infobox_data):
		type = ""

		if "type" in infobox_data and infobox_data["type"] != "":
			type = infobox_data["type"]
			type = EventUtils.remove_templates(type).lower()

		return type

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

	def extract_text(extracted, ent_data, debugger):
		infobox_name = ent_data["infobox_name"]

		name = ""
		type = extracted["type"]

		if infobox_name != "" and infobox_name != "event":
			name = infobox_name.lower()

		if type:
			extracted["type"] = type
		else:
			extracted["type"] = name
		
		if name == "election" and type:
			extracted["type"] = f"{type} election"
		else:
			extracted["type"] = "election"

		return extracted

