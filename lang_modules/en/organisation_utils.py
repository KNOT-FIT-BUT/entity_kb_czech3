
import re

from lang_modules.en.core_utils import CoreUtils

class OrganisationUtils:

	KEYWORDS = {
		"type": ["type"]
	}

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
