
import unittest
import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from ent_settlement import EntSettlement
from debugger import Debugger

class SettlementTests(unittest.TestCase):

	def __init__(self, *args, **kwargs):
		super(SettlementTests, self).__init__(*args, **kwargs)
		self.d = Debugger()
		self.person = EntSettlement(
			"title", 
			"country", 
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

	def test_country(self):
		pass

	def test_area(self):
		pass

	def test_population(self):
		pass

	def test_coords(self):
		pass

if __name__ == "__main__":
	unittest.main()