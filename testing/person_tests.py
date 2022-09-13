
import unittest
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from ent_person import EntPerson
from debugger import Debugger

class PersonTests(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super(PersonTests, self).__init__(*args, **kwargs)
		self.d = Debugger()
		self.person = EntPerson(
			"title", 
			"person", 
			"https://en.wikipedia.org/wiki/",
			{
				"data": {},
				"name": "infobox_name",
				"categories": [],
				"paragraph": "",
				"coords": "",
				"images": []
			},
			{},
			["redirects"],
			"sentence",
			self.d
		)
				
	def test_dates(self):
		infobox_values = [
			
		]

		for i in infobox_values:
			value, result = i
			self.person.infobox_data["birth_date"] = value
			self.person.infobox_data["datum narození"] = value
			self.person.assign_places()
			self.assertEqual(self.person.birth_place, result)

	def test_places(self):
		infobox_values = [
			# en
			("Beijing, China", "Beijing, China"),
			("[[Gangtok, Sikkim|Gangtok]], [[Sikkim]], India", "Gangtok, Sikkim, India"),
			("[[Brooklyn]], New York, United States", "Brooklyn, New York, United States"),
			("[[San Francisco]], [[California]], [[United States of America|USA]]", "San Francisco, California, USA"),
			("[[Virginia]], United States [[File:Flag of the United States.svg|20px]]", "Virginia, United States"),
			("[[Belgrade]], [[Kingdom of Serbs, Croats and Slovenes]]{{small|(now [[Serbia]])}}", "Belgrade, Kingdom of Serbs, Croats and Slovenes(now Serbia)"),
			("[[Yerevan]], [[Armenian Soviet Socialist Republic|Armenian SSR]], {{nowrap|Soviet Union}}", "Yerevan, Armenian SSR, Soviet Union"),
			# cs
			("[[Benátky nad Jizerou]] {{Vlajka a název|Rakousko-Uhersko}}", "Benátky nad Jizerou Rakousko-Uhersko"),
			("{{flagicon|TCH}} [[Praha]], [[Československo]]", "TCH Praha, Československo"),
			("[[Zlín]] {{nowrap|{{flagicon|Protektorát Čechy a Morava}} [[Protektorát Čechy a Morava]]}}", "Zlín Protektorát Čechy a Morava Protektorát Čechy a Morava"),
			("[[Novo mesto]] [[Soubor: Flag of Yugoslavia (1918–1943).svg |20px]] [[Království Srbů, Chorvatů a Slovinců]]", "Novo mesto Království Srbů, Chorvatů a Slovinců"),
			("[[Královo Pole ]]  {{Vlajka a název|Rakousko-Uhersko}}", "Královo Pole Rakousko-Uhersko")
		]

		for i in infobox_values:
			value, result = i
			self.person.infobox_data["birth_place"] = value
			self.person.infobox_data["místo narození"] = value
			self.person.assign_places()
			self.assertEqual(self.person.birth_place, result)

	def test_gender(self):
		infobox_values = [
			# en
			("male", "M"),
			("female", "F"),
			
			("change lang", "cs"),
			# cs
			("muž", "M"),
			("žena", "F")
		]

		categories = [
			# en
			("female authors", "F"),
			("female fictional characters", "F"),
			("male poets", "M"),
			("male scientists", "M"),
			
			("change lang", "cs"),
			# cs
			("muži", "M"),
			("ženy", "F")	
		]

		for i in infobox_values:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				continue
			self.person.infobox_data["gender"] = value
			self.person.infobox_data["pohlaví"] = value
			self.person.assign_gender()
			self.assertEqual(self.person.gender, result)

		for c in categories:
			value, result = i
			if value == "change lang":
				self.person.lang = result
				continue
			self.person.categories = [c]
			self.person.assign_gender()
			self.assertEqual(self.person.gender, result)

	def test_jobs(self):
		infobox_values = [
			# cs
			("režisér, scenárista, producent", "režisér|scenárista|producent"),
			("[[herec]], [[moderátor (profese)|moderátor]], [[komik]], [[bavič]], [[humorista]], [[tanečník]], [[baleťák]], [[zpěvák]], [[dabér]], [[scenárista]]", "herec|moderátor|komik|bavič|humorista|tanečník|baleťák|zpěvák|dabér|scenárista"),
			("[[zpěvák]], muzikálový herec a&nbsp;zpěvák", "zpěvák|muzikálový herec a zpěvák"),
			# en
			("{{hlist | Computer programmer | businessperson}}", "Computer programmer|businessperson"),
			("[[Programmer]]; [[Politician]]", "Programmer|Politician"),
			("{{indented plainlist|\n* [[Invention|Inventor]]\n* [[Cryptography|Cryptographer]]}}", "Inventor|Cryptographer"),
			("{{ubl|[[Mad scientist|Scientist]]|Inventor|Leader of the Citadel (formerly)|Freedom fighter (formerly)}}", "Scientist|Inventor|Leader of the Citadel|Freedom fighter"),
			("{{unbulleted list|Scholar|Librarian |Poet |Inventor}}", "Scholar|Librarian|Poet|Inventor")
		]

		for i in infobox_values:
			value, result = i
			self.person.infobox_data["occupation"] = value
			self.person.infobox_data["profese"] = value
			self.person.assign_jobs()
			self.assertEqual(self.person.jobs, result)	

	def test_nationality(self):
		infobox_values = [
			# en
			("{{flag|United States}}", "United States"),
			("[[United States|American]]", "American"),
			("[[flag|United States]]", "United States"),
			("Dreamlander, Maruvian", "Dreamlander|Maruvian"),
			("[[French people|French]]-[[Austrians|Austrian]]", "French|Austrian"),
			("British/Oceanian (in film)", "British|Oceanian"),
			# cs
			("{{flagicon|CRO}} [[Chorvati|chorvatká]]", "chorvatká"),
			("[[Češi|česká]]", "česká")
		]

		for i in infobox_values:
			value, result = i
			self.person.infobox_data["nationality"] = value
			self.person.infobox_data["národnost"] = value
			self.person.assign_nationality()
			self.assertEqual(self.person.nationality, result)	


if __name__ == "__main__":
	unittest.main()