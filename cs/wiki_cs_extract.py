#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, os, sys, argparse, time
from datetime import datetime
import xml.etree.cElementTree as CElTree
from multiprocessing import Pool
from itertools import repeat
import mwparserfromhell as parser
from collections import Counter

from debugger import Debugger

from ent_person import *
from ent_country import *
from ent_settlement import *
from ent_watercourse import *
from ent_waterarea import *
from ent_geo import *

class WikiExtract(object):
	def __init__(self):
		self.console_args = None
		self.d = Debugger()
		# self.entities = dict()

	@staticmethod
	def create_head_kb():
		entities = [
			"<person>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tGENDER\t{e}DATE OF BIRTH\tPLACE OF BIRTH\t{e}DATE OF DEATH\tPLACE OF DEATH\t{m}JOBS\t{m}NATIONALITY\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
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
			# <organisation>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tFOUNDED\tCANCELLED\tORGANIZATION TYPE\tLOCATION\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n",
			# "<event>ID\tTYPE\tNAME\t{m}ALIASES\t{m}REDIRECTS\tSTART\tEND\tLOCATION\tDESCRIPTION\tORIGINAL_WIKINAME\t{gm[http://athena3.fit.vutbr.cz/kb/images/]}IMAGE\t{ui}WIKIPEDIA LINK\tWIKI BACKLINKS\tWIKI HITS\tWIKI PRIMARY SENSE\tSCORE WIKI\tSCORE METRICS\tCONFIDENCE\n"
		]

		with open("HEAD-KB", "w", encoding="utf-8") as fl:
			for entity in entities:
				fl.write(entity)

	@staticmethod
	def get_url(title):
		wiki_url = "https://cs.wikipedia.org/wiki/" + title.replace(" ", "_")

		return wiki_url

	@staticmethod
	def is_entity(title):
		# speciální stránky Wikipedie nepojednávají o entitách
		if title.startswith(
			(
				"wikipedie:",
				"redaktor:",
				"soubor:",
				"mediawiki:",
				"šablona:",
				"pomoc:",
				"kategorie:",
				"speciální:",
				"portál:",
				"modul:",
				"seznam",
				"geografie",
				"společenstvo",
			)
		):
			return False

		# stránky pro data (datumy) nepojednávají o entitách
		if re.search(r"^\d{1,2}\. [^\W\d_]+$", title):
			return False

		# ostatní stránky mohou pojednávat o entitách
		return True

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

	def parse_args(self):
		parser = argparse.ArgumentParser()
		parser.add_argument(
			"-I",
			"--indir",
			default="/mnt/minerva1/nlp/corpora_datasets/monolingual/czech/wikipedia/",
			type=str,
			help="Directory, where input files are located (applied for files withoud directory location only).",
		)
		parser.add_argument(
			"-l",
			"--lang",
			default="cs",
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

		self.pages_dump_fpath = self.get_dump_fpath(
			self.console_args.pages, "{}wiki-{}-pages-articles.xml"
		)
		self.geotags_dump_fpath = self.get_dump_fpath(
			self.console_args.geotags, "{}wiki-{}-geo_tags.sql"
		)
		self.redirects_dump_fpath = self.get_dump_fpath(
			self.console_args.redirects, "redirects_from_{}wiki-{}-pages-articles.xml"
		)
		if self.console_args.dev:
			self.console_args._kb_stability = "dev"
		elif self.console_args.test:
			self.console_args._kb_stability = "test"
		else:
			self.console_args._kb_stability = ""

	def assign_version(self):
		str_kb_stability = ""
		if self.console_args._kb_stability:
			str_kb_stability = f"-{self.console_args._kb_stability}"
			
		try:
			target = os.readlink(self.pages_dump_fpath)
			matches = re.search(self.console_args.lang + r"wiki-([0-9]{8})-", target)
			if matches:
				dump_version = matches[1]
		except OSError:
			try:
				target = os.readlink(self.redirects_dump_fpath)
				matches = re.search(
					self.console_args.lang + r"wiki-([0-9]{8})-", target
				)
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
				self.d.print("loading redirects")
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
				self.d.print("loading langmap")
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
				self.d.print("loading first sentences")
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
		except OSError:
			self.d.print("entity identification patterns were not found - exiting...")
			# exit(1)

		return patterns

	def parse_xml_dump(self):

		redirects = self.load_redirects(self.redirects_dump_fpath)
		langmap = self.load_langmap("langmap_fpath")
		first_sentences = self.load_first_sentences("sentence_fpath")
		patterns = self.load_patterns(os.path.join(os.path.dirname(sys.argv[0]), "json/identification.json"))

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
							is_entity = self.is_entity(child.text.lower())
							if is_entity:
								title = child.text
						# získá text stránky
						elif "revision" in child.tag:
							for grandchild in child:
								if "text" in grandchild.tag and is_entity and grandchild.text:
									if re.search(r"{{[^}]*?(?:rozcestník)(?:\|[^}]*?)?}}", grandchild.text, re.I):
										self.d.update("found disambiguation")
										break                    

									# nalezení nové entity
									link = self.get_url(title)
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
			"geo":          EntGeo
			# "organisation": None,
			# "event":        None
		}

		if count != 0:
			key = identification[0][0]
			if key in entities:
				entity = entities[key](title, key, self.get_url(title), extraction, langmap, redirects, sentence, self.d)
				entity.assign_values()
				return repr(entity)

		# TODO: log unidentified
		return None

	##
	# @brief tries to extract infobox, first paragraph, categories and coordinates
	# @param content - string containing page content 
	# @return dictionary of extracted entity data
	#
	# uses the mwparserfromhell library
	def extract_entity_data(self, content):

		content = self.remove_references(content)
		# content = self.remove_not_improtant(content)

		result = {
			"found": False,
			"name": "",
			"data": dict(),
			"paragraph": "",
			"categories": [],
			"coords": ""
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
				# TODO: fix names e.g.: "- spisovatel"
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
			for s in split:
				if s.startswith("'''") or s.startswith("The '''"):
					result["paragraph"] = s.strip()
					break

		# extract categories
		lines = content.splitlines()
		for line in lines:
			if line.startswith("[[Kategorie:"):
				result["categories"].append(line[12:-2].strip())
		
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

	@staticmethod
	def remove_references(content):
		
		delimiter = "<"
		text_parts = content.split(delimiter)
		re_tag = r"^/?[^ />]+(?=[ />])"
		delete_mode = False
		tag_close = None

		for i_part, text_part in enumerate(text_parts[1:], 1):  # skipping first one which is not begin of tag
			if delete_mode and tag_close:
				if text_part.startswith(tag_close):
					text_parts[i_part] = text_part[len(tag_close) :]
					delete_mode = False
				else:
					text_parts[i_part] = ""
			else:
				matched_tag = re.search(re_tag, text_part)
				if matched_tag:
					matched_tag = matched_tag.group(0)
					if matched_tag in ["nowiki", "ref", "refereces"]:
						tag_close = "/" + matched_tag + ">"
						text_len = len(text_part)
						text_part = re.sub(r"^.*?/>", "", text_part, 1)
						if text_len == len(text_part):
							delete_mode = True
						text_parts[i_part] = "" if delete_mode else text_part
					else:
						tag_close = None
						text_parts[i_part] = delimiter + text_part

		et_cont = "".join(text_parts)
		et_cont = re.sub(r"{{citace[^}]+?}}", "", et_cont, flags=re.I | re.S)
		et_cont = re.sub(r"{{cite[^}]+?}}", "", et_cont, flags=re.I)
		et_cont = re.sub(
			r"{{#tag:ref\s*\|(?:[^\|\[{]|\[\[[^\]]+\]\]|(?<!\[)\[[^\[\]]+\]|{{[^}]+}})*(\|[^}]+)?}}",
			"",
			et_cont,
			flags=re.I | re.S,
		)
		et_cont = re.sub(r"<!--.+?-->", "", et_cont, flags=re.DOTALL)

		link_multilines = re.findall(
			r"\[\[(?:Soubor|File)(?:(?:[^\[\]\n{]|{{[^}]+}}|\[\[[^\]]+\]\])*\n)+(?:[^\[\]\n{]|{{[^}]+}}|\[\[[^\]]+\]\])*\]\]",
			et_cont,
			flags=re.S,
		)
		for link_multiline in link_multilines:
			fixed_link_multiline = link_multiline.replace("\n", " ")
			et_cont = et_cont.replace(link_multiline, fixed_link_multiline)
		et_cont = re.sub(r"(<br(?:\s*/)?>)\n", r"\1", et_cont, flags=re.S)
		et_cont = re.sub(
			r"{\|(?!\s+class=(?:\"|')infobox(?:\"|')).*?\|}", "", et_cont, flags=re.S
		)
		
		return et_cont

# hlavní část programu
if __name__ == "__main__":
	wiki_extract = WikiExtract()

	wiki_extract.parse_args()
	wiki_extract.create_head_kb()
	wiki_extract.parse_xml_dump()
	wiki_extract.assign_version()

	wiki_extract.d.log()
