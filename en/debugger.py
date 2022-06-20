# TUI debugging for easier testing and usage

import datetime
import json

# ideas:
# pause extraction every time interesting entity is found / inform about it
# print messages with color depending on their importance / meaning 

class Debugger:
	def __init__(self):
		# add debug mode on/off switch
		with open("log", 'r+') as f:
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
		with open("log", "a") as f:
			f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")

	# logs entity information
	@staticmethod
	def log_entity(entity, prefix):
		entities = {}
		with open("entities.json", "r") as file:
			entities = json.load(file)
		
		entity_data = entity.split("\t")
		with open("log", "a") as f:
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
		SCORE = 20

		entity_data = entity.split("\t")
		score = 0
		for d in entity_data:
			if d == "":
				score += 1
		if score > SCORE:
			self.log_entity(entity, prefix)