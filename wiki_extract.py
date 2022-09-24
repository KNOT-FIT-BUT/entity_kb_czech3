#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
# @mainpage Entity KB project index page
# see https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_english5 for more information...

##
# @file wiki_extract.py
# @brief main script that contains WikiExtract class that extracts and identifies entities
# 
# @section how_it_works how it works
# - parses arguments
# - creates head and version
# - parses wikipedia xml dump
# - logs errors and statistics to a file
# @section parsing_xml_dump parsing the xml dump
# - loads the redirect, first sentence, identification patterns and langmap files
# - goes through the xml file and identifies entities
# - for each entity:
#   - extracts important data
#   - identifies the entity
#   - assigns a class to the entity
# - outputs extracted entities into a file
# 
# @author created by Jan Kapsa (xkapsa00)
# @date 26.07.2022

import os, re, argparse, time, json, sys

from debugger import Debugger as debug
import xml.etree.cElementTree as CElTree
from datetime import datetime
from multiprocessing import Pool
from itertools import repeat
from collections import Counter
import mwparserfromhell as parser

from ent_person import EntPerson
from ent_country import EntCountry
from ent_settlement import EntSettlement
from ent_waterarea import EntWaterArea
from ent_watercourse import EntWaterCourse
from ent_geo import EntGeo
from ent_organisation import EntOrganisation
from ent_event import EntEvent

from lang_modules.en.core_utils import CoreUtils as EnCoreUtils
from lang_modules.cs.core_utils import CoreUtils as CsCoreUtils

LANG_MAP = {"cz": "cs"}

utils = {
	"en": EnCoreUtils,
	"cs": CsCoreUtils
}

##
# @class WikiExtract
# @brief main class of the project, one istance is created to execute the main functions
class WikiExtract(object):
	##
	# @brief initializes the console_args variable and debugger class
	def __init__(self):
		self.console_args = None
		self.d = debug()
		# self.first_sentence_version = "20210101"
		# self.first_sentences_path = f"/mnt/minerva1/nlp/corpora_datasets/monolingual/english/wikipedia/1st_sentences_from_enwiki-20210101-pages-articles.tsv"
		self.first_sentences_path = f"testing_data/xml/1st_sentences_from_enwiki-20210101-pages-articles.tsv"

	##
	# @brief parses the console arguments
	def parse_args(self):
		parser = argparse.ArgumentParser()
		parser.add_argument(
			"-I",
			"--indir",
			default="/mnt/minerva1/nlp/corpora_datasets/monolingual/english/wikipedia/",
			type=str,
			help="Directory, where input files are located (applied for files withoud directory location only).",
		)
		parser.add_argument(
			"-l",
			"--lang",
			default="en",
			type=str,
			help="Language of processing also used for input files, when defined by version (by default) and not by files (default: %(default)s).",
		)
		parser.add_argument(
			"-d",
			"--dump",
			default="latest",
			type=str,
			help='Dump version to process (in format "yyyymmdd"; default: %(default)s).',
		)
		parser.add_argument(
			"-m",
			default=2,
			type=int,
			help="Number of processors of multiprocessing.Pool() for entity processing.",
		)
		parser.add_argument(
			"-g",
			"--geotags",
			action="store",
			type=str,
			help="Source file of wiki geo tags (with GPS locations) dump.",
		)
		parser.add_argument(
			"-p",
			"--pages",
			action="store",
			type=str,
			help="Source file of wiki pages dump.",
		)
		parser.add_argument(
			"-r",
			"--redirects",
			action="store",
			type=str,
			help="Source file of wiki redirects dump.",
		)
		parser.add_argument(
			"--dev",
			action="store_true",
			help="Development version of KB",
		)
		parser.add_argument(
			"--test",
			action="store_true",
			help="Test version of KB",
		)
		
		self.console_args = parser.parse_args()

		if self.console_args.m < 1:
			self.console_args.m = 1

		self.console_args.lang = self.console_args.lang.lower()
		if self.console_args.lang in LANG_MAP:
			self.console_args.lang = LANG_MAP[self.console_args.lang]

		self.pages_dump_fpath = self.get_dump_fpath(self.console_args.pages, "{}wiki-{}-pages-articles.xml")
		self.geotags_dump_fpath = self.get_dump_fpath(self.console_args.geotags, "{}wiki-{}-geo_tags.sql")
		self.redirects_dump_fpath = self.get_dump_fpath(self.console_args.redirects, "redirects_from_{}wiki-{}-pages-articles.tsv")
		self.console_args._kb_stability = ""

		if self.console_args.dev:
			self.console_args._kb_stability = "dev"
		elif self.console_args.test:
			self.console_args._kb_stability = "test"

	##
	# @brief creates a path to the dump file
	# @param dump_file
	# @param dump_file_mask
	# @return string file path
	def get_dump_fpath(self, dump_file, dump_file_mask):
		if dump_file is None:
			dump_file = dump_file_mask.format(
				self.console_args.lang, self.console_args.dump
			)
		elif dump_file[0] == "/":
			return dump_file
		elif dump_file[0] == "." and (dump_file[1] == "/" or dump_file[1:3] == "./"):
			return os.path.join(os.getcwd(), dump_file)

		return os.path.join(self.console_args.indir, dump_file)

	##
	# @brief creates a wikipedia link given the page name
	# @param page - string containing page title
	# @return wikipedia link
	def get_link(self, page):
		wiki_link = page.replace(" ", "_")
		return f"https://{self.console_args.lang}.wikipedia.org/wiki/{wiki_link}"

	##
	# @brief creates the HEAD-KB file
	# HEAD-KB file contains individual fields of each entity
	@staticmethod
	def create_head_kb():
		entities = [
			"<person>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<person:artist>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<person:fictional>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<person:group>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<country>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<country:former>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<settlement>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tCOUNTRY\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<watercourse>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tLENGTH\tAREA\tSTREAMFLOW\tSOURCE_LOC\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<waterarea>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tAREA\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:relief>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:waterfall>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tTOTAL HEIGHT\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:island>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\t{m}CONTINENT\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:peninsula>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<geo:continent>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tLATITUDE\tLONGITUDE\tAREA\tPOPULATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<organisation>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tFOUNDED\tCANCELLED\tORGANISATION_TYPE\tLOCATION\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			"<event>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tSTART\tEND\tLOCATION\tEVENT_TYPE\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n"
		]		
		
		with open("HEAD-KB", "w", encoding="utf-8") as file:
			for entity in entities:
				file.write(entity)

	##
	# @brief creates the VERSION file
	def assign_version(self):
		str_kb_stability = f"-{self.console_args._kb_stability}" if self.console_args._kb_stability else ""
		
		try:
			target = os.readlink(self.pages_dump_fpath)
			matches = re.search(self.console_args.lang + r"wiki-([0-9]{8})-", target)
			if matches:
				dump_version = matches[1]
		except OSError:
			try:
				target = os.readlink(self.redirects_dump_fpath)
				matches = re.search(self.console_args.lang + r"wiki-([0-9]{8})-", target)
				if matches:
					dump_version = matches[1]
			except OSError:
				dump_version = self.console_args.dump
		
		with open("VERSION", "w") as f:
			f.write("{}_{}-{}{}".format(
				self.console_args.lang,
				dump_version,
				int(round(time.time())),
				str_kb_stability,
			))

	##
	# @brief loads redirects
	# @param redirects_fpath path to the file with extracted redirects
	# @return dictionary with redirects
	def load_redirects(self, redirects_fpath):
		redirects = dict()
		
		try:
			with open(redirects_fpath, "r") as f:
				self.d.update("loading redirects")
				i = 0
				for line in f:
					i += 1
					self.d.update(i)
					redirect_from, redirect_to = line.strip().split("\t")

					if redirect_to not in redirects:
						redirects[redirect_to] = [redirect_from]
					else:
						redirects[redirect_to].append(redirect_from)

				self.d.print(f"loaded redirects ({i})")
		except OSError:            
			self.d.print("redirect file was not found - skipping...")
		
		return redirects

	##
	# @brief loads langmap
	# @param langmap_fpath path to the file with langmap
	# @return dictionary with langmap
	def load_langmap(self, langmap_fpath):
		langmap = dict()
		
		try:
			with open(langmap_fpath, "r") as file:
				self.d.update("loading langmap")
				langmap = json.load(file)
				self.d.print("loaded langmap")
		except OSError:
			self.d.print(f"langmap file 'langmap.json' was not found")
			self.d.print(f"please generate langmap.json (use generate_langmap.json)")
			# exit(1)

		return langmap

	##
	# @brief loads first sentences
	# @param senteces_fpath path to the file with extracted first sentences
	# @return dictionary with first sentences
	def load_first_sentences(self, senteces_fpath):
		first_sentences = dict()

		try:
			with open(senteces_fpath, "r") as f:
				self.d.update("loading first sentences")
				i = 0
				for line in f:
					i += 1
					self.d.update(i)
					split = line.strip().split("\t")
					link = split[0]
					sentence = split[1] if len(split) > 1 else ""
					first_sentences[link] = sentence

				self.d.print(f"loaded first sentences ({i})")
		except OSError:            
			self.d.print("first sentence file was not found - skipping...")
		
		return first_sentences

	##
	# @brief loads patterns for entity recognition
	# @param patterns_fpath path to the file with patterns
	# @return dictionary with patterns
	def load_patterns(self, patterns_fpath):
		patterns = dict()

		try:
			with open(patterns_fpath, "r") as file:
				patterns = json.load(file)
			self.d.print("loaded identification patterns")
		except OSError:
			self.d.print("entity identification patterns were not found - exiting...")
			# exit(1)

		return patterns

	## 
	# @brief loads redirects, first sentences, langmap and patterns, then parses xml dump
	def parse_xml_dump(self):
		
		redirects = self.load_redirects(self.redirects_dump_fpath)
		langmap = self.load_langmap(os.path.join(os.path.dirname(sys.argv[0]), f"json/langmap_{self.console_args.lang}.json"))
		first_sentences = self.load_first_sentences("sentence_fpath")
		patterns = self.load_patterns(os.path.join(os.path.dirname(sys.argv[0]), f"json/{self.console_args.lang}_identification.json"))

		# xml parser
		context = CElTree.iterparse(self.pages_dump_fpath, events=("start", "end"))

		ent_data = []

		curr_page_cnt = 0
		all_page_cnt = 0
		ent_count = 0

		# LOOP_CYCLE = skript bude číst a extrahovat data po blocích o velikosti [LOOP_CYCLE]
		LOOP_CYCLE = 4000
		debug_limit_hit = False

		with open("kb", "a+", encoding="utf-8") as file:
			file.truncate(0)
			event, root = next(context)
			for event, elem in context:

				if debug_limit_hit:
					break

				# hledá <page> element
				if event == "end" and "page" in elem.tag:
					# xml -> <page> -> <title>
					# xml -> <page> -> <revision>
					is_entity = False
					title = ""

					for child in elem:
						# získá title stránky
						if "title" in child.tag:
							is_entity = utils[self.console_args.lang].is_entity(child.text.lower())
							if is_entity:
								title = child.text
						# získá text stránky
						elif "revision" in child.tag:
							for grandchild in child:
								if "text" in grandchild.tag and is_entity and grandchild.text:
									if re.search(utils[self.console_args.lang].DISAMBIG_PATTERN, grandchild.text, re.I):
										self.d.update("found disambiguation")
										break                    

									# nalezení nové entity
									link = self.get_link(title)
									ent_data.append((
										title, 
										grandchild.text, 
										redirects[link] if link in redirects else [], 
										first_sentences[link] if link in first_sentences else ""
									))

									curr_page_cnt += 1
									all_page_cnt += 1

									self.d.update(f"found new page ({all_page_cnt})")

									if self.d.debug_limit is not None and all_page_cnt >= self.d.debug_limit:
										self.d.print(f"debug limit hit (number of pages: {all_page_cnt})")
										debug_limit_hit = True
										break

									if curr_page_cnt == LOOP_CYCLE:
										ent_count += self.output(file, ent_data, langmap, patterns)
										ent_data.clear()
										curr_page_cnt = 0    
						elif "redirect" in child.tag:
							self.d.update(f"found redirect ({all_page_cnt})")
							break

					root.clear()

			if len(ent_data):
				ent_count += self.output(file, ent_data, langmap, patterns)

		self.d.print("----------------------------", print_time=False)
		self.d.print(f"parsed xml dump (number of pages: {all_page_cnt})", print_time=False)
		self.d.print(f"processed {ent_count} entities", print_time=False)

	##
	# @brief extracts the entities with multiprocessing and outputs the data to a file
	# @param file - output file ("kb" file)
	# @param ent_data - ordered array of tuples with entity data
	# @param langmap - dictionary of language abbreviations
	# @param patterns - dictionary containing identification patterns
	# @return number of pages that were identified as entities (count of extracted entities)
	def output(self, file, ent_data, langmap, patterns):
		if len(ent_data):
			start_time = datetime.now()

			pool = Pool(processes=self.console_args.m)
			serialized_entities = pool.starmap(
				self.process_entity,
				zip(ent_data, repeat(langmap), repeat(patterns))                    
			)
			l = list(filter(None, serialized_entities))
			file.write("\n".join(l) + "\n")
			pool.close()
			pool.join()
			count = len(l)

			end_time = datetime.now()
			tdelta = end_time - start_time
			self.d.print(f"processed {count} entities (in {self.d.pretty_time_delta(tdelta.total_seconds())})")
			self.d.log_message(f"time_avg,{tdelta},{len(ent_data)};")
			return count

	##
	# @brief extracts entity data, identifies the type of the entity and assigns a class
	# @param ent_data - dictionary with entity data (title, page content, ...)
	# @param langmap - dictionary of language abbreviations
	# @param patterns - dictionary containing identification patterns
	# @return tab separated string with entity data or None if entity is unidentified
	def process_entity(self, ent_data, langmap, patterns):
		title, content, redirects, sentence = ent_data

		self.d.update(f"processing {title}")

		extraction = self.extract_entity_data(content)
		identification = self.identify_entity(title, extraction, patterns).most_common()

		count = 0
		for _, value in identification:
			count += value


		entities = {
			"person":       EntPerson,
			"country":      EntCountry,
			"settlement":   EntSettlement,
			"waterarea":    EntWaterArea,
			"watercourse":  EntWaterCourse,
			"geo":          EntGeo,
			"organisation": EntOrganisation,
			"event":        EntEvent
		}

		if count != 0:
			key = identification[0][0]
			if key in entities:
				entity = entities[key](title, key, self.get_link(title), extraction, langmap, redirects, sentence, self.d)
				entity.assign_values(self.console_args.lang)
				return repr(entity)
		
		# self.d.log_message(f"Error: unidentified page: {title}")
		return None

	##
	# @brief tries to extract infobox, first paragraph, categories and coordinates
	# @param content - string containing page content 
	# @return dictionary of extracted entity data
	#
	# uses the mwparserfromhell library
	def extract_entity_data(self, content):

		content = self.remove_not_improtant(content)

		result = {
			"found": False,
			"name": "",
			"data": dict(),
			"paragraph": "",
			"categories": [],
			"coords": "",
			"images": []
		}

		wikicode = parser.parse(content)
		templates = wikicode.filter_templates()

		infobox = None

		# look for infobox
		for t in templates:
			name = t.name.lower().strip()
			if name.startswith("infobox") and infobox is None:
				infobox = t
				name = name.split()
				name.pop(0)
				name = " ".join(name)
				result["found"] = True
				# fix names e.g.: "- spisovatel"
				name = name.strip()
				if name and name[0] == '-':
					name = name[1:].strip()								
				result["name"] = name
			elif "coord" in name or "coords" in name:
				result["coords"] = str(t)

		# extract infobox
		if result["found"]:
			for p in infobox.params:
				field = p.strip()
				field = [item.strip() for item in field.split("=")]
				key = field.pop(0).lower()
				value = "=".join(field)
				result["data"][key] = value

		# extract first paragraph
		sections = wikicode.get_sections()
		if len(sections):
			section = sections[0]
			templates = section.filter_templates()
			
			for t in templates:
				if t.name.lower().startswith("infobox"):
					section.remove(t)
					break
			
			split = [s for s in section.strip().split("\n") if s != ""]
			while len(split):
				s = split.pop(0)
				if re.search(r"^(?:'''|The ''')", s, flags=re.I):
					s += f" {' '.join(split)}"
					result["paragraph"] = s.strip()
					break
		else:
			self.d.log_message("Error: no first section found")

		# extract categories
		lines = content.splitlines()
		for line in lines:
			# categories
			pattern = utils[self.console_args.lang].CATEGORY_PATTERN
			match = re.search(pattern, line, re.I)
			if match:
				result["categories"].append(match.group(1).strip())
				continue

			# images
			match = re.search(r"\[\[(?:file|soubor):([^\]]*?)\|[^\]]*?\]\]", line, re.I)
			if match:
				value = match.group(1).strip()
				if re.search(r"\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)$", value, re.I):
					result["images"].append(value)
		
		return result

	##
	# @brief uses patterns to score the entity, prefix with the highest score is later chosen as the entity identification
	# @param title - string containing page title 
	# @param extracted - dictionary with extracted entity data (infobox, categories, ...)
	# @param patterns - dictionary containing identification patterns
	# @return Counter instance with identification scores
	#
	# entity is given a point for each matched pattern
	# it looks at categories, infobox names, titles and infobox fields
	# these patterns are located in a en/json/identification.json file
	#
	# @todo better algorithm for faster performance
	# @todo score weight system
	@staticmethod
	def identify_entity(title, extracted, patterns):
		counter = Counter({key: 0 for key in patterns.keys()})

		# categories
		for c in extracted["categories"]:
			for entity in patterns.keys():
				for p in patterns[entity]["categories"]:
					if re.search(p, c, re.I):
						# print("matched category")
						counter[entity] += 1

		# infobox names
		for entity in patterns.keys():
			for p in patterns[entity]["names"]:
				if re.search(p, extracted["name"], re.I):
					# print("matched name")
					counter[entity] += 1

		# titles
		for entity in patterns.keys():
			for p in patterns[entity]["titles"]:
				if re.search(p, title, re.I):
					# print("matched title")
					counter[entity] += 1

		# infobox fields
		for entity in patterns.keys():
			for field in patterns[entity]["fields"]:
				if field in extracted["data"]:
					# print("matched field")
					counter[entity] += 1

		return counter

	##
	# @brief deletes references, comments, etc. from a page content
	# @param page_content - string containing page_content
	# @return page content withou reference tags, comments, etc...
	def remove_not_improtant(self, page_content):
		clean_content = page_content

		# remove comments
		clean_content = re.sub(r"<!--.*?-->", "", clean_content, flags=re.DOTALL)

		# remove references
		clean_content = re.sub(r"<ref[^<]*?/>", "", clean_content, flags=re.DOTALL)
		clean_content = re.sub(r"<ref(?:.*?)?>.*?</ref>", "", clean_content, flags=re.DOTALL)

		# remove {{efn ... }}, {{refn ...}}, ...
		clean_content = self.remove_ref_templates(clean_content)
		
		# remove break lines
		clean_content = re.sub(r"<br\s*?/>", "  ", clean_content, flags=re.DOTALL)
		clean_content = re.sub(r"<br>", "  ", clean_content, flags=re.DOTALL)
		clean_content = re.sub(r"<.*?/?>", "", clean_content, flags=re.DOTALL)

		return clean_content

	@staticmethod
	def remove_ref_templates(content):
		patterns = [
			r"\{\{efn",
			r"\{\{refn",
			r"\{\{citation",
			r"\{\{notetag",
			r"\{\{snf",
			r"\{\{#tag:ref",
			r"\{\{ref label"
		]
		
		spans = []

		for p in patterns:
			match = re.finditer(p, content, flags=re.I)
			for m in match:				
				start = m.span()[0]
				end = start
				indent = 0
				for c in content[start:]:
					if c == '{':
						indent += 1
					elif c == '}':
						indent -= 1
					end += 1
					if indent == 0:
						break
				spans.append((start, end))
		
		for span in sorted(spans, reverse=True):
			start, end = span
			# debug.log_message(f"removed: {content[start:end]}")
			content = content[:start] + content[end:]
		
		content = re.sub(r"[ \t]+", " ", content)
				
		return content

if __name__ == "__main__":
	wiki_extract = WikiExtract()
	
	wiki_extract.parse_args()
	wiki_extract.create_head_kb()
	wiki_extract.assign_version()    
	wiki_extract.parse_xml_dump()
	wiki_extract.d.log()