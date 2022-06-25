# TUI debugging for easier testing and usage

import datetime
import json

# ideas:
# pause extraction every time interesting entity is found / inform about it
# print messages with color depending on their importance / meaning 

SCORE = 20
ENTITIES = "entities.json"
LOG = "log"

class Debugger:
	def __init__(self):
		# add debug mode on/off switch
		self.debug_limit = None
		with open(LOG, 'r+') as f:
			f.truncate(0)

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
	def log_message(message):
		with open(LOG, "a") as f:
			# f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
			f.write(f"{message}\n")

	# logs entity information
	@staticmethod
	def log_entity(entity, prefix):
		entities = {}
		with open(ENTITIES, "r") as file:
			entities = json.load(file)
		
		entity_data = entity.split("\t")
		with open(LOG, "a") as f:
			f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] logging entity\n")
			empty = []
			for i in range(len(entity_data)):
				if entity_data[i] != "":
					f.write(f"{entities[prefix][i]}: {entity_data[i]}\n")
				else:
					empty.append(entities[prefix][i])
			f.write(f"empty: {', '.join(empty)}\n\n")
	
	# checks if entity is mostly empty (implies badly identified entity)
	def check_empty(self, entity, prefix):
		entity_data = entity.split("\t")
		score = 0
		for d in entity_data:
			if d == "":
				score += 1
		if score > SCORE:
			self.log_entity(entity, prefix)

	@staticmethod
	def log_infobox(infobox):
		if len(infobox.items()) > 0:
			with open(LOG, "a") as f:
				f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] logging infobox\n")
				for key, item in infobox.items():
					if item != "":
						f.write(f"{key}: {item}\n")
				f.write("\n\n")			