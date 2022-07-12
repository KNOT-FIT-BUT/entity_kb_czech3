# TUI debugging for easier testing and usage

import datetime
import json
from collections import Counter
import sys
import os

# ideas:
# pause extraction every time interesting entity is found / inform about it
# print messages with color depending on their importance / meaning 

SCORE = 10
ENTITIES_FP	= "json/entities.json"

class Debugger:
	def __init__(self):
		# TODO: add debug mode on/off switch
		# TODO: stats
		
		self.debug_limit = None

		# categories
		self.infobox_names = set()
		self.category_counter = Counter()

		# identification
		self.id_count = 0
		self.id_sum = 0
		self.entities = {}
		with open(os.path.join(os.path.dirname(sys.argv[0]), ENTITIES_FP), "r") as f:
			self.entities = json.load(f)

	# clears currently updating message and prints a message with a new line 
	@staticmethod
	def print(msg):
		print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\033[K")

	# updates (clears) current line and writes new message 
	@staticmethod
	def update(msg):
		print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\033[K", end="\r")

	# logs data into a file
	@staticmethod
	def log_message(message, print_time=False):		
		if print_time:
			print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}", file=sys.stderr)
		else:
			print(f"{message}", file=sys.stderr)

	# logs entity information
	def log_entity(self, entity, prefix):
		data = []

		entity_data = entity.split("\t")
		data.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] logging entity")
		empty = []
		for i in range(len(entity_data)):
			if entity_data[i] != "":
				data.append(f"  {self.entities[prefix][i]}: {entity_data[i]}")
			else:
				empty.append(self.entities[prefix][i])
		data.append(f"  empty: {', '.join(empty)}")
		self.log_message("\n".join(data))
	
	# checks if entity is mostly empty (implies badly identified entity)
	def check_empty(self, entity, prefix):
		entity_data = entity.split("\t")
		score = 0
		for d in entity_data:
			if d == "":
				score += 1
		if score > SCORE:
			self.log_entity(entity, prefix)

	def log_extraction(self, title, extraction, flags=(False, False, False)):
		
		data = []

		data.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] logging entity extraction")
		data.append(f"title: {title}")

		# flags[0] == infobox extraction
		if flags[0]:
			if extraction["found"]:
				data.append("infobox:")
				empty = []
				for key, value in extraction["data"].items():
					if value != "":
						value = value.replace("\n", "")
						data.append(f"  {key}: {value}")
					else:
						empty.append(key)
				data.append(f"  empty: {', '.join(empty)}")
			else:
				data.append("infobox not found")
		
		# flags[1] == category extraction
		if flags[1]:
			data.append("categories:")
			for c in extraction["categories"]:
				data.append(f"  {c}")
		
		# flags[2] == paragraph extraction
		if flags[2]:
			data.append("paragraph:")
			data.append(f"  {extraction['paragraph']}")
		
		self.log_message("\n".join(data))


	def log_identification(self, title, identification):
		# identification is a Counter
		self.log_message(f"identification of {title}:")
		for key, value in identification:
			self.log_message(f"{key}: {value}")

	def stats(self):

		log = []

		# stats_id_avg
		id_count = 0
		id_sum = 0
		id_counter = Counter()

		# gender:birth_date:birth_place:death_date:death_place:jobs:nationality
		ent = {
			"person": [0, 0, 0, 0, 0, 0, 0, 0],
			"country": [0, 0, 0, 0, 0],
			"settlement": [0, 0, 0, 0, 0, 0]
		}
		ent_names = {
			"person": "gender:birth_date:birth_place:death_date:death_place:jobs:nationality",
			"country": "latitude:longtitude:area:population",
			"settlement": "country:latitude:longtitude:area:population"
		}

		with open(os.path.join(os.path.dirname(sys.argv[0]), "out/kb.out"), "r") as f:
			lines = f.readlines()
			for line in lines:
				split = line.split(",")

				# format: stats_id_avg,<type>,<number>
				if split[0] == "stats_id_avg":
					id_count += 1
					# FIXME: id_sum += int(split[2])
					id_counter[split[1]] += 1
				elif split[0] == "stats_ent":
					ent[split[1]][-1] += 1
					values = split[2].split("$")
					for i in range(len(values)):
						if values[i] != "":
							ent[split[1]][i] += 1
				else:
					log.append(line)

		with open(os.path.join(os.path.dirname(sys.argv[0]), "log/kb.log"), "w") as f:
			f.writelines(log)

		with open(os.path.join(os.path.dirname(sys.argv[0]), "log/stats.log"), "w") as f:
			f.write("identification:\n\n")
			if id_count != 0:
				f.write(f"count: {id_count}\n")
				f.write(f"sum: {id_sum}\n")
				f.write(f"avg: {round(id_sum/id_count, 2)}\n\n")
			for key, value in id_counter.most_common():
				f.write("{:<15} {}\n".format(key, value))

			f.write("\nentities:\n")
			for key in ent.keys():
				f.write("\n{:<15} {}\n".format(key.upper(), ent[key][-1]))
				names = ent_names[key].split(":")
				for i in range(len(ent[key])-1):
					f.write("{:<15} {}%\n".format(names[i], round(ent[key][i]/ent[key][-1]*100,2)))