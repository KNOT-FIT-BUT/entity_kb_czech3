import re
import json
import requests

def generate():

	r = requests.get("https://en.wikipedia.org/w/index.php?title=Special:Export&pages=List_of_ISO_639-2_codes")
	lines = r.text.split("\n")

	items = []
	for line in lines:
		if line.startswith("| {{iso639-2"):
			items.append(line)
	
	langs = dict()

	for item in items:
		split = item.split("||")
		split[3] = split[3].strip()
		if split[3] != "":
			split[0] = re.sub(r".*{{iso639-2\|(...)(?:-...)?}}.*", r"\1", split[0])
			
			split[4] = re.sub(r"\[\[.*\|(.*)\]\]", r"\1", split[4])
			split[4] = re.sub(r"\[|\]", "", split[4])
			split[4] = re.sub(r"&nbsp;", " ", split[4])
			split[4] = re.sub(r",.*$", "", split[4])
			split[4] = re.sub(r"\(.*\)", "", split[4])

			split[4] = split[4].strip()
			
			langs[split[0]] = f"{split[3]}|{split[4]}"

	with open("langmap.json", "w", encoding="utf8") as f:
		json.dump(langs, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
	generate()