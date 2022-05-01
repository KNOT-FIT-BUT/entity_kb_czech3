
import re

def gen_stats():

	scores = dict()
	sum_total = 0
	count_total = 0

	head = dict()

	with open("outputs/HEAD-KB", "r") as file:
		for line in file:
			m = re.search(r"<(.*?)>", line)
			line = re.sub(r"<.*?>|{.*?}|\n", "", line)
			split = line.split("\t")
			if m:
				scores[m.group(1)] = [0] * (len(split) + 2)
				head[m.group(1)] = split
				head[m.group(1)].insert(0, "COUNT")
				head[m.group(1)].insert(0, "SUM")


	with open("outputs/KBstatsMetrics.all", "r") as file:
		for line in file:
			split = line.split("\t")
			type = split[1]
			score = split[-2]

			scores[type][0] += float(score)
			scores[type][1] += 1

			for i in range(len(split)):
				if split[i] != "":
					scores[type][i+2] += 1

		for key, value in scores.items():
			if value[1] == 0:
				continue
			avg = round(value[0]/value[1],2)
			avg = str(avg)
			sum_total += value[0]
			count_total += value[1]
			if len(avg) == 4:
				avg += "0"
			print(f"{avg}%\t\t{key}")

		for key, value in scores.items():
			if value[1] == 0:
				continue
			print(f"\n-- {key} --")
			for i in range(len(value)):
				if head[key][i] in (
						"SUM", 
						"COUNT", 
						"ID", 
						"TYPE", 
						"NAME", 
						"DESCRIPTION", 
						"ORIGINAL_WIKINAME", 
						"WIKIPEDIA LINK", 
						"WIKI BACKLINKS", 
						"WIKI HITS", 
						"WIKI PRIMARY SENSE",
						"SCORE WIKI",
						"SCORE METRICS",
						"CONFIDENCE"):
					continue
				number = round(scores[key][i]*100/scores[key][1], 2)
				number = str(number)
				if float(number) < 10:
					number = f"0{number}"
				if len(number) == 4:
					number += "0"
				print(f"{number}%\t{head[key][i]}")
				
		
		avg = round(sum_total/count_total,2)
		avg = str(avg)
		if len(avg) == 4:
				avg += "0"
		print("-----------------------")
		print(f"{avg}%\t\ttotal")
		print(f"total entities: {count_total}")
		


if __name__ == "__main__":
	gen_stats()