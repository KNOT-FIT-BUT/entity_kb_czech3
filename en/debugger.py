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

		# time
		self.start_time = datetime.datetime.now()

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
	def print(message, print_time=True):
		if print_time:
			message = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}"
		print(f"{message}\033[K")

	# updates (clears) current line and writes new message 
	@staticmethod
	def update(msg):
		print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\033[K", end="\r")

	# logs data into a file
	@staticmethod
	def log_message(message, print_time=False):		
		if print_time:
			message = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}"
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
		end_time = datetime.datetime.now()
		tdelta = end_time - self.start_time
		self.print(f"completed extraction in {self.pretty_time_delta(tdelta.total_seconds())}", print_time=False)
		self.log_message(f"time_total,{tdelta};")

		log = []

		with open(os.path.join(os.path.dirname(sys.argv[0]), "out/kb.out"), "r") as f:
			lines = f.readlines()
			for line in lines:
				msg = line.split(";")[0]
				msg = msg.split(",")
				if msg[0] not in ["id_stats", "time_avg", "time_total"]:
					log.append(line)

		with open(os.path.join(os.path.dirname(sys.argv[0]), "log/kb.log"), "w") as f:
			f.writelines(log)

	@staticmethod
	def pretty_time_delta(seconds):
		seconds = int(seconds)
		days, seconds = divmod(seconds, 86400)
		hours, seconds = divmod(seconds, 3600)
		minutes, seconds = divmod(seconds, 60)
		if days > 0:
			return '%dd%dh%dm%ds' % (days, hours, minutes, seconds)
		elif hours > 0:
			return '%dh%dm%ds' % (hours, minutes, seconds)
		elif minutes > 0:
			return '%dm%ds' % (minutes, seconds)
		else:
			return '%ds' % (seconds,)