
import re

from lang_modules.en.core_utils import CoreUtils

class OrganisationUtils:

	@staticmethod
	def extract_infobox(ent_data, debugger):

		extraction = {
			"founded": "",
			"cancelled": "",
			"location": "",
			"type": ""
		}

		infobox_data = ent_data["infobox_data"]

		extraction["founded"], extraction["cancelled"] = OrganisationUtils.assign_dates(infobox_data)
		extraction["location"] = OrganisationUtils.assign_location(infobox_data)
		extraction["type"] = OrganisationUtils.assign_type(infobox_data)

		return extraction

	##
    # @brief extracts and assigns founded and cancelled variables from infobox
	@staticmethod
	def assign_dates(infobox_data):
		
		founded = ""
		cancelled = ""

		keys = ["formation", "foundation", "founded", "fouded_date", "established"]

		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				date = CoreUtils.extract_date(data)
				if len(date) >= 1:
					founded = date[0]
					break

		keys = ["defunct", "banned", "dissolved"]
		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				date = CoreUtils.extract_date(data)
				if len(date) >= 1:
					cancelled = date[0]
					break

		keys = ["active", "dates"]
		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				splitter = '-'
				if '–' in data:
					splitter = '–'
				data = data.split(splitter)
				if len(data) == 2:
					date = CoreUtils.extract_date(data[0])
					if founded == "":
						founded = date[0]
					date = CoreUtils.extract_date(data[1])
					if cancelled == "":
						cancelled = date[0]
					break

		return (founded, cancelled)

	##
    # @brief extracts and assigns location from infobox
	@staticmethod
	def assign_location(infobox_data):
		result = ""
		location = ""
		country = ""
		city = ""

		keys = ["location", "headquarters", "hq_location", "area"]
		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = OrganisationUtils.remove_templates(data)
				location = data
				break
		
		keys = ["location_country", "country", "hq_location_country"]
		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = OrganisationUtils.remove_templates(data)
				country = data
				break

		keys = ["location_city", "hq_location_city"]
		for key in keys:
			if key in infobox_data and infobox_data[key] != "":
				data = infobox_data[key]
				data = OrganisationUtils.remove_templates(data)
				city = data
				break

		if city != "" and country != "":
			result = f"{city}, {country}"
		else:
			if location != "":
				result = location
			elif country != "":
				result = country
			else:
				result = city
			
		return result

	##
    # @brief extracts and assigns type from infobox
	@staticmethod
	def assign_type(infobox_data):
		type = ""

		if "type" in infobox_data and infobox_data["type"] != "":
			data = infobox_data["type"]
			data = OrganisationUtils.remove_templates(data)
			type = data
		
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

	@staticmethod
	def extract_text(extracted, ent_data, debugger):

		infobox_name = ent_data["infobox_name"]

		if not extracted["type"]:
			if infobox_name:
				if infobox_name.lower() != "organization":
					extracted["type"] = infobox_name

		return extracted