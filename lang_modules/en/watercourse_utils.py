
import re

from lang_modules.en.core_utils import CoreUtils

class WatercourseUtils:

	@staticmethod
	def extract_infobox(ent_data, debugger):
		extraction = {
			"latitude": "",
			"longitude": "",
			"continents": "",
			"area": "",
			"length": "",
			"streamflow": "",
			"source_loc": ""
		}

		infobox_data, title = (
			ent_data["infobox_data"],
			ent_data["title"]	
		)

		extraction["latitude"], extraction["longitude"] = CoreUtils.assign_coordinates(infobox_data, debugger)
		extraction["area"] = CoreUtils.assign_area(infobox_data,  debugger)
		extraction["length"] = WatercourseUtils.assign_length(infobox_data, debugger)
		extraction["streamflow"] = WatercourseUtils.assign_streamflow(infobox_data, debugger)
		extraction["source_loc"] = WatercourseUtils.assign_source_loc(infobox_data)

		return extraction


	# def assign_continents(self):
	# 	# cant match from infobox
	# 	pass

	##
    # @brief extracts and assigns length from infobox
	@staticmethod
	def assign_length(infobox_data, debugger):
		length = ""

		# | length = {{convert|352|km|mi|abbr=on}}
		if "length" in infobox_data:
			length_match = infobox_data["length"]
			if length_match != "":
				match = re.search(r"{{(?:[Cc]onvert|cvt)\|([0-9.]+)\|(.+?)(?:\|.+?)?}}", length_match)
				if match:
					length = CoreUtils.convert_units(match.group(1), match.group(2), debugger)
		
		#print(f"{self.title}: did not find length")
		return length
		
	##
    # @brief extracts and assigns streamflow from infobox
	@staticmethod
	def assign_streamflow(infobox_data, debugger):
		
		streamflow = ""
		
		# | discharge1_avg     = {{convert|593000|cuft/s|m3/s|abbr=on}}
		if "discharge1_avg" in infobox_data:
			streamflow_match = infobox_data["discharge1_avg"]
			if streamflow_match != "":
				streamflow_match = streamflow_match.replace(",", "")
				match = re.search(r"{{.*?\|([0-9.,]+)\|((?:\w|\/)+).*?}}", streamflow_match)
				if match:
					streamflow = CoreUtils.convert_units(match.group(1), match.group(2), debugger)
				else:
					debugger.log_message(f"did not match streamflow ({streamflow_match})")
		
		#print(f"{self.title}: streamflow empty or not found")
		return streamflow

	##
    # @brief extracts and assigns source location from infobox
	@staticmethod
	def assign_source_loc(infobox_data):
		
		source = ""

		# format: source1_location = near [[Hollenthon, Austria|Hollenthon]], [[Lower Austria]]
		if "source1_location" in infobox_data:
			source = infobox_data["source1_location"]
			if source != "":
				source = re.sub(r"\[\[([^\]]+?)\|([^\]]+?)\]\]", r"\2", source)
				source = re.sub(r"{{[^}]+?\|([^}]+?)(?:\|[^}]+?)?}}", r"\1", source)
				source = re.sub(r"\[|\]|\'", "", source)
		
		#print(f"{self.title}: did not found source location")
		return source

	@staticmethod
	def extract_text(extracted, ent_data, debugger):
		coords = ent_data["coords"]

		if coords != "" and (not extracted["latitude"] or not extracted["longitude"]):
			coords = CoreUtils.get_coordinates(coords, debugger)
			if all(coords):
				extracted["latitude"], extracted["longitude"] = coords

		return extracted