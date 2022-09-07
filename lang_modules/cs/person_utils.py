
import re, regex

from lang_modules.cs.core_utils import CoreUtils

from lang_modules.cs.libs.natToKB import *
from lang_modules.cs.libs.DictOfUniqueDict import *
from lang_modules.cs.libs.UniqueDict import KEY_LANG, LANG_ORIG, LANG_UNKNOWN

class PersonUtils:

	KEYWORDS = {
		"birth_place": 	["místo narození", "místo_narození"],
		"death_place": 	["místo úmrtí", "místo_úmrtí"],
		"gender": 		["pohlaví"],
		"male": 		"muž",
		"female": 		"žena",
		"jobs":			["profese", "zaměstnání", "povolání"],
		"nationality":	["národnost"]
	}

	##
	# @brief assigns prefix to the person entity
	#
	# person, person:fictional or person:group
	@staticmethod
	def assign_prefix(person):
		# prefix - fiktivní osoby
		# TODO: temp content? joining categories?
		content = "\n".join(person.categories)
		if (re.search(r"hrdinové\s+a\s+postavy\s+řecké\s+mytologie", content, re.I,) or 
			re.search(r"bohové", content, re.I) or 
			re.search(r"postavy", content, re.I)):			
			return "person:fictional" 

		# prefix - groups
		natToKB = NatToKB()
		nationalities = natToKB.get_nationalities()

		name_without_location = re.sub(r"\s+(?:ze?|of|von)\s+.*", "", person.title, flags=re.I)
		a_and_neighbours = re.search(r"((?:[^ ])+)\s+a(?:nd)?\s+((?:[^ ])+)", name_without_location)
		if a_and_neighbours:
			if (a_and_neighbours.group(1) not in nationalities or a_and_neighbours.group(2) not in nationalities):
				# else Kateřina Řecká a Dánská" is regular person
				return "person:group"
		
		return "person"

	@classmethod
	def extract_infobox(cls, ent_data, debugger):
		extraction = {
			"aliases": "",
			"nationality": "",
		}

		title, categories, infobox_data, infobox_name = (
			ent_data["title"],
			ent_data["categories"],
			ent_data["infobox_data"],
			ent_data["infobox_name"]
		)

		extraction["aliases"] = cls.assign_aliases(infobox_data, infobox_name, title)
		
		return extraction

	# @staticmethod
	# def assign_gender(infobox_data, categories):
	# 	# pohlaví
	# 	# TODO: temp content
	# 	gender = ""
	# 	content = "\n".join(categories)

	# 	if re.search(r"muži", content, re.I):
	# 		gender = "M"
	# 	elif re.search(r"ženy", content, re.I):
	# 		gender = "F"
	# 	else:
	# 		# pohlaví as a field in the infobox
	# 		if "pohlaví" in infobox_data and infobox_data["pohlaví"]:
	# 			value = infobox_data["pohlaví"].lower().strip()
	# 			if value == "muž":
	# 				gender = "M"
	# 			elif value == "žena":
	# 				gender = "F"

	# 	return gender

	@classmethod
	def assign_dates(cls, person):
		birth_date = ""
		death_date = ""
		
		# Date of birth
		keys = ["datum narození", "datum_narození"]
		for key in keys:
			if key in person.infobox_data and person.infobox_data[key]:
				value = person.infobox_data[key]
				value = CoreUtils.del_redundant_text(value)
				birth_date = cls._convert_date(value, True)
				break

		# Date of death
		keys = ["datum úmrtí", "datum_úmrtí"]
		for key in keys:
			if key in person.infobox_data and person.infobox_data[key]:
				value = person.infobox_data[key]
				value = CoreUtils.del_redundant_text(value)
				death_date = cls._convert_date(value, False)
				break

		return (birth_date, death_date)

	@classmethod
	def assign_aliases(cls, infobox_data, infobox_name, title):
		NT_PSEUDO = "pseudo"
		NT_NICK = "nick"
		
		aliases = DictOfUniqueDict()
		n_marked_czech = 0
		first_alias = None
		
		# Aliases - infobox extraction
		
		keys = ["jiná jména", "rodné jméno", "celé jméno", "úplné jméno", "posmrtné jméno", "chrámové jméno", "trůnní jméno",
			"pseudonym", "přezdívka", "alias"]

		for key in keys:
			if key in infobox_data and infobox_data[key]:
				value = infobox_data[key]
				if re.search(r"nezveřejněn|neznám", value, re.I):
					continue
				
				nametype = None
				tmp_alias = value
				tmp_name_type = key

				if tmp_name_type == "pseudonym":
					nametype = NT_PSEUDO
				elif tmp_name_type in ["přezdívka", "alias"]:
					nametype = NT_NICK
				elif tmp_name_type == "rodné jméno":
					alias_spaces = len(re.findall(r"[^\s]+\s+[^\s]+", tmp_alias))
					if not alias_spaces:
						tmp_alias_new, was_replaced = re.subn(
							r"(?<=\s)(?:ze?|of|von)\s+.*",
							tmp_alias,
							title,
							flags=re.I,
						)
						if was_replaced:
							tmp_alias = tmp_alias_new
						else:
							tmp_alias = re.sub(r"[^\s]+$", tmp_alias, title)

				# https://cs.wikipedia.org/wiki/Marie_Gabriela_Bavorská =>   | celé jméno = německyː ''Marie Gabrielle Mathilde Isabelle Therese Antoinette Sabine Herzogin in Bayern''
				tmp_alias = re.sub(r"^\s*německyː\s*", "", tmp_alias, flags=re.I)
				# https://cs.wikipedia.org/wiki/T%C3%BArin =>   | přezdívka = viz [[Túrin#Jména, přezdívky a tituly|Jména, přezdívky a tituly]]
				tmp_alias = re.sub(r"^\s*(?:viz\s+)?\[\[[^\]]+\]\]", "", tmp_alias, flags=re.I)  
				tmp_alias = CoreUtils.del_redundant_text(tmp_alias)
				custom_data = {"infobox_name": infobox_name}
				result, n_marked_czech, first_alias = CoreUtils.get_aliases(tmp_alias, aliases, cls.custom_transform_alias, custom_data, nametype=nametype) 
				aliases.update(result)
		
		aliases = CoreUtils.serialize_aliases(aliases, title, n_marked_czech, first_alias)

		return aliases

	# TODO aliases - extract_text
	@classmethod
	def extract_text(cls, extracted, ent_data, debugger):
		
		title, first_paragraph = (
			ent_data["title"],
			ent_data["first_paragraph"]
		)

		# # Female surname variants with or without suffix "-ová"
		# if extracted["gender"] == "F":
		# 	female_variant = (title[:-3] if title[-3:] == "ová" else (title + "ová"))
		# 	# if redirects and female_variant in redirects:
		# 	# 	# TODO: fix this
		# 	# 	# self.aliases[female_variant][KEY_LANG] = (self.LANG_CZECH if self.title[-3:] == "ová" else LANG_UNKNOWN)
		# 	# 	return extracted

		abbrs = "".join((
			r"(?<!\s(?:tzv|at[pd]|roz))",
			r"(?<!\s(?:apod|(?:ku|na|po)př|příp))",
			r"(?<!\s[amt]j)",
			r"(?<!\d)",
		))
		match = re.search(
			r".*?'''.+?'''.*?\s(?:byl[aiy]?|je|jsou|(?:patř|působ)(?:í|il|ila|ily)|stal).*?"
			+ abbrs
			+ "\.(?![^[]*?\]\])",
			first_paragraph,
		)
		if match:
			text = cls.get_first_sentence(CoreUtils.del_redundant_text(match.group(0), ", "), title)

			# TODO: do this?
			# if not self.description:
			# 	self.description = text

			# získání data/místa narození/úmrtí z první věty - začátek
			# (* 2000)
			if not extracted["birth_date"]:
				rexp = re.search(r"\(\s*\*\s*(\d+)\s*\)", text)
				if rexp and rexp.group(1):
					extracted["birth_date"] = cls._convert_date(rexp.group(1), True)

			# (* 1. ledna 2000)
			if not extracted["birth_date"]:
				rexp = re.search(r"\(\s*\*\s*(\d+\.\s*\w+\.?\s+\d{1,4})\s*\)", text)
				if rexp and rexp.group(1):
					extracted["birth_date"] = cls._convert_date(rexp.group(1), True)

			# (* 1. ledna 2000, Brno), (* 1. ledna 200 Brno, Česká republika)
			if not extracted["birth_date"] or not extracted["birth_place"]:
				rexp = re.search(
					r"\(\s*\*\s*(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])\s*(?![\-–—−])\)",
					text,
				)
				if rexp:
					if rexp.group(1) and not extracted["birth_date"]:
						extracted["birth_date"] = cls._convert_date(rexp.group(1), True)
					if rexp.group(2) and not extracted["birth_place"]:
						extracted["birth_place"] = cls.get_place(rexp.group(2))

			# (* 2000 – † 2018), (* 2000, Brno - † 2018 Brno, Česká republika)
			if (
				not extracted["birth_date"]
				or not extracted["death_date"]
				or not extracted["birth_place"]
				or not extracted["death_place"]
			):
				rexp = re.search(
					r"\(\s*(?:\*\s*)?(\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*[\-–—−]\s*(?:†\s*)?(\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*\)",
					text,
				)
				if rexp:
					if rexp.group(1) and not extracted["birth_date"]:
						extracted["birth_date"] = cls._convert_date(rexp.group(1), True)
					if rexp.group(2) and not extracted["birth_place"]:
						extracted["birth_place"] = cls.get_place(rexp.group(2))
					if rexp.group(3) and not extracted["death_date"]:
						extracted["death_date"] = cls._convert_date(rexp.group(3), False)
					if rexp.group(4) and not extracted["death_place"]:
						extracted["death_place"] = cls.get_place(rexp.group(4))

			# (* 1. ledna 2000 – † 1. ledna 2018), (* 1. ledna 2000, Brno - † 1. ledna 2018 Brno, Česká republika)
			if (
				not extracted["birth_date"]
				or not extracted["death_date"]
				or not extracted["birth_place"]
				or not extracted["death_place"]
			):
				rexp = re.search(
					r"\(\s*(?:\*\s*)?(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*[\-–—−]\s*(?:†\s*)?(\d+\.\s*\w+\.?\s+\d{1,4})\s*(?:,\s*)?([^\W\d_][\w\s\-–—−,]+[^\W\d_])?\s*\)",
					text,
				)
				if rexp:
					if rexp.group(1) and not extracted["birth_date"]:
						extracted["birth_date"] = cls._convert_date(rexp.group(1), True)
					if rexp.group(2) and not extracted["birth_place"]:
						extracted["birth_place"] = cls.get_place(rexp.group(2))
					if rexp.group(3) and not extracted["death_date"]:
						extracted["death_date"] = cls._convert_date(rexp.group(3), False)
					if rexp.group(4) and not extracted["death_place"]:
						extracted["death_place"] = cls.get_place(rexp.group(4))
			# získání data/místa narození/úmrtí z první věty - konec

			# TODO: different langmap?
			# tmp_first_sentence = match.group(0)
			# fs_first_aliases = []
			# # extrakce alternativních pojmenování z první věty
			# #  '''Jiří''' (též '''Jura''') '''Mandel''' -> vygenerovat "Jiří Mandel" a "Jura Mandel" (negenerovat "Jiří", "Jura", "Mandel")
			# tmp_fs_first_aliases = regex.search(
			#     r"^((?:'{3}(?:[\"\p{L} ]|'(?!''))+'{3}\s+)+)\((?:(?:někdy|nebo)?\s*(?:také|též|rozená))?\s*(?:('{3}[^\)]+'{3}))?(?:'(?!'')|[^\)])*\)\s*((?:'{3}\p{L}+'{3}\s+)*)(.*)",
			#     tmp_first_sentence, flags=re.I,
			# )
			
			# if tmp_fs_first_aliases:
			# 	fs_fa_before_bracket = tmp_fs_first_aliases.group(1).strip()
			# 	fs_fa_after_bracket = tmp_fs_first_aliases.group(3).strip()
			# 	if fs_fa_after_bracket:
			# 		fs_first_aliases.append(
			# 			fs_fa_before_bracket + " " + fs_fa_after_bracket
			# 		)
			# 		if tmp_fs_first_aliases.group(2):
			# 			name_variants = re.findall(
			# 				r"'{3}(.+?)'{3}", tmp_fs_first_aliases.group(2).strip()
			# 			)
			# 			if name_variants:
			# 				for name_variant in name_variants:
			# 					fs_first_aliases.append(
			# 						re.sub("[^ ]+$", name_variant, fs_fa_before_bracket)
			# 						+ " " + fs_fa_after_bracket
			# 					)
			# 	else:
			# 		if tmp_fs_first_aliases.group(2):
			# 			fs_first_aliases += re.findall(r"'{3}(.+?)'{3}", tmp_fs_first_aliases.group(2).strip())
			# 	tmp_first_sentence = tmp_fs_first_aliases.group(4)
			
			# else:
			# 	#  '''Jiří''' '''Jindra''' -> vygenerovat "Jiří Jindra" (negenerovat "Jiří" a "Jindra")
			# 	tmp_fs_first_aliases = regex.search(
			# 	    r"^((?:'{3}\p{L}+'{3}\s+)+)(.*)", tmp_first_sentence
			# 	)
			# 	if tmp_fs_first_aliases:
			# 		fs_first_aliases.append(tmp_fs_first_aliases.group(1).strip())
			# 		tmp_first_sentence = tmp_fs_first_aliases.group(2).strip()

			# fs_aliases_lang_links = []
			# link_lang_aliases = re.findall(
			# 	r"\[\[(?:[^\[]* )?([^\[\] |]+)(?:\|(?:[^\]]* )?([^\] ]+))?\]\]\s*('{3}.+?'{3})",
			# 	tmp_first_sentence,
			# 	flags=re.I,
			# )
			# link_lang_aliases += re.findall(
			# 	r"(" + "|".join(self.langmap.keys()) + r")():?\s+('{3}.+?'{3})",
			# 	tmp_first_sentence,
			# 	flags=re.I,
			# )
			# for link_lang_alias in link_lang_aliases:
			# 	for i_group in [0, 1]:
			# 		if (
			# 			link_lang_alias[i_group]
			# 			and link_lang_alias[i_group] in self.langmap
			# 		):
			# 			fs_aliases_lang_links.append(
			# 				"{{{{Vjazyce|{}}}}} {}".format(
			# 					self.langmap[link_lang_alias[i_group]],
			# 					link_lang_alias[2],
			# 				)
			# 			)
			# 			tmp_first_sentence = tmp_first_sentence.replace(
			# 				link_lang_alias[2], ""
			# 			)
			# 			break
			# fs_aliases = re.findall(
			# 	r"((?:{{(?:Cj|Cizojazyčně|Vjazyce2?)[^}]+}}\s+)?'{3}.+?'{3})",
			# 	tmp_first_sentence,
			# 	flags=re.I,
			# )
			# fs_aliases += [
			# 	" ".join(
			# 		str
			# 		for tup in re.findall(
			# 			r"([Ss]v(?:\.|at[áéíý]))\s+'{3}(.+?)'{3}",
			# 			tmp_first_sentence,
			# 		)
			# 		for str in tup
			# 	)
			# ]
			# fs_aliases += fs_aliases_lang_links
			# fs_aliases += fs_first_aliases

			# for fs_alias in fs_aliases:
			# 	self.aliases.update(
			# 		self.get_aliases(self.del_redundant_text(fs_alias).strip("'"))
			# 	)		

		return extracted

	##
	# @brief Převádí místo narození/úmrtí osoby do jednotného formátu.
	# @param place - místo narození/úmrtí osoby (str)
	# @param is_birth - určuje, zda se jedná o místo narození, či úmrtí (bool)
	@staticmethod
	def get_place(place):
		place = re.sub(r"{{Vlajka a název\|(.*?)(?:\|.*?)?}}", r"\1", place, flags=re.I)
		place = re.sub(
			r"{{(?:vjazyce2|cizojazyčně|audio|cj)\|.*?\|(.+?)}}",
			r"\1",
			place,
			flags=re.I,
		)
		place = re.sub(r"{{malé\|(.*?)}}", r"\1", place, flags=re.I)
		place = re.sub(r"{{.*?}}", "", place)
		place = re.sub(r"<br(?: /)?>", " ", place)
		place = re.sub(r"<.*?>", "", place)
		place = re.sub(
			r"\[\[(?:Soubor|File):.*?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)[^\]]*\]\]",
			"",
			place,
			flags=re.I,
		)
		place = re.sub(r"\d+\s*px", "", place, flags=re.I)
		place = re.sub(
			r"(?:(?:,\s*)?\(.*?věk.*?\)$|\(.*?věk.*?\)(?:,\s*)?)", "", place, flags=re.I
		)
		place = re.sub(r"\(.*?let.*?\)", "", place, flags=re.I)
		place = re.sub(r",{2,}", ",", place)
		place = re.sub(r"(\]\])[^,]", r"\1, ", place)
		place = CoreUtils.del_redundant_text(place)
		place = re.sub(r"[{}<>\[\]]", "", place)
		place = re.sub(r"\s+", " ", place).strip().strip(",")
		return place

	##
	# @brief Převádí zaměstnání osoby do jednotného formátu.
	# @param job - zaměstnání osoby (str)
	@staticmethod
	def get_jobs(job):
		
		job = re.sub(
			r"(?:Soubor|File):.*?\.(?:jpe?g|png|gif|bmp|ico|tif|tga|svg)(?:\|[\w\s]+)?\|[\w\s]+\|[\w\s]+(?:,\s*)?",
			"",
			job,
			flags=re.I,
		)
		job = re.sub(r"\d+\s*px", "", job, flags=re.I)
		job = re.sub(r"^[\s,]+", "", job)
		job = re.sub(r"\[.*?\]", "", job)
		job = re.sub(r"\s*/\s*", ", ", job)
		job = re.sub(r"\s+", " ", job).strip().strip(".,;")

		if ";" in job:
			job = re.sub(r"\s*;\s*", "|", job)
		else:
			job = re.sub(r"\s*,\s*", "|", job)

		return job

	##
	# @brief Převádí národnost osoby do jednotného formátu
	# @param nationality - národnost osoby (str)	
	@staticmethod
	def get_nationality(nationality):
		nationality = re.sub(
			r"{{Vlajka a název\|(.*?)(?:\|.*?)?}}", r"\1", nationality, flags=re.I
		)
		nationality = re.sub(r"{{malé\|(.*?)}}", r"\1", nationality, flags=re.I)
		nationality = re.sub(r"{{.*?}}", "", nationality)
		nationality = re.sub(r"<.*?>", "", nationality)
		nationality = re.sub(r"(.*?)\|.*$", r"\1", nationality)
		nationality = re.sub(r"\d+\s*px", "", nationality, flags=re.I)
		nationality = re.sub(r"\(.*?\)", "", nationality)
		nationality = re.sub(r"\s+", " ", nationality).strip().strip(".,;")
		nationality = re.sub(
			r"\s*[,;/]\s*|\s+(?:či|[\-–—−]|a|nebo)\s+", "|", nationality
		)

		return nationality

	##
	# @brief Převádí první větu stránky do jednotného formátu a získává z ní popis a datum a místo narození/úmrtí.
	# @param text - první věta stránky (str)
	@classmethod
	def get_first_sentence(cls, text, title):
		# TODO: refactorize
		text = re.sub(r"{{(?:vjazyce2|cizojazyčně|audio|cj)\|.*?\|(.+?)}}", r"\1", text, flags=re.I)
		text = re.sub(r"{{IPA\d?\|(.+?)}}", r"\1", text, flags=re.I)
		text = re.sub(r"{{výslovnost\|(.+?)\|.*?}}", r"\1", text, flags=re.I)
		text = cls._subx(
			r".*?{{\s*datum[\s_]+(?:narození|úmrtí)\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*",
			lambda x: cls._regex_date(x, 3),
			text,
			flags=re.I,
		)
		text = cls._subx(
			r".*?{{\s*JULGREGDATUM\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)[^}]*}}.*",
			lambda x: cls._regex_date(x, 4),
			text,
			flags=re.I,
		)
		text = re.sub(
			r"{{čínsky(.+?)}}",
			lambda x: re.sub(
				"(?:znaky|pchin-jin|tradiční|zjednodušené|pinyin)\s*=\s*(.*?)(?:\||}})",
				r"\1 ",
				x.group(1),
				flags=re.I,
			),
			text,
			flags=re.I,
		)
		text = re.sub(r"{{malé\|(.*?)}}", r"\1", text, flags=re.I)
		text = re.sub(r"{{PAGENAME}}", title, text, flags=re.I)
		text = re.sub(r"{{.*?}}", "", text)
		text = re.sub(r"<.*?>", "", text)
		text = re.sub(r"\s+", " ", text).strip()
		text = re.sub(r"^\s*}}", "", text)  # Eliminate the end of a template

		return text

	##
	# @brief Umožňuje provádět vlastní transformace aliasů entity do jednotného formátu.
	# @param alias - alternativní pojmenování entity (str)
	# TODO aliases
	@staticmethod
	def custom_transform_alias(alias, data):
		
		re_titles_religious = []
		if data["infobox_name"] in ["křesťanský vůdce", "světec"]:
			# https://cs.wikipedia.org/wiki/Seznam_zkratek_c%C3%ADrkevn%C3%ADch_%C5%99%C3%A1d%C5%AF_a_kongregac%C3%AD
			# https://cs.qwe.wiki/wiki/List_of_ecclesiastical_abbreviations#Abbreviations_of_titles_of_the_principal_religious_orders_and_congregations_of_priests
			# http://www.katolik.cz/otazky/ot.asp?ot=657
			re_titles_religious = [
				"A(?:\. ?)?(?:F|M)\.?",  # AF, AM
				"A(?:\. ?)?(?:B(?:\. ?)?)?A\.?",  # AA, ABA
				"A(?:\. ?)?C(?:\. ?)?S\.?",  # ACS
				"A(?:\. ?)?M(?:\. ?)?B(?:\. ?)?V\.?",  # AMBV
				"B\.?",  # B
				"C(?:\. ?)?C\.?(?: ?G\.?)?",  # CC, CCG
				"C(?:\. ?)?F(?:\. ?)?C\.?",  # CFC
				"C(?:\. ?)?F(?:\. ?)?Ss(?:\. ?)?S\.?",  # CFSsS
				"C(?:\. ?)?C(?:\. ?)?R(?:\. ?)?R(?:\. ?)?M(?:\. ?)?M\.?",  # CCRRMM
				"C(?:\. ?)?(?:J(?:\. ?)?)?M\.?",  # CJM, CM
				"C(?:\. ?)?M(?:\. ?)?F\.?",  # CMF
				"C(?:\. ?)?M(?:\. ?)?S(?:\. ?)?Sp(?:\. ?)?S\.?",  # CMSSpS
				"C(?:\. ?)?P\.?(?: ?P(?:\. ?)?S\.?)?",  # CP, CPPS
				"Č(?:\. ?)?R\.?",  # ČR
				"C(?:\. ?)?R(?:\. ?)?C(?:\. ?)?S\.?",  # CRCS
				"C(?:\. ?)?R(?:\. ?)?I(?:\. ?)?C\.?",  # CRIC
				"C(?:\. ?)?R(?:\. ?)?(?:L|M|T|V)\.?",  # CRL, CRM, CRT, CRV
				"C(?:\. ?)?R(?:\. ?)?M(?:\. ?)?(?:D|I)\.?",  # CRMD, CRMI
				"C(?:\. ?)?R(?:\. ?)?(?:S(?:\. ?)?)?P\.?",  # CRP, CRSP
				"C(?:\. ?)?S(?:\. ?)?(?:B|C|J|P|V)\.?",  # CSB, CSC, CSJ, CSP, CSV
				"C(?:\. ?)?S(?:\. ?)?C(?:\. ?)?D(?:\. ?)?I(?:\. ?)?J\.?",  # CSCDIJ
				"C(?:\. ?)?S(?:\. ?)?S(?:\. ?)?E\.?",  # CSSE
				"C(?:\. ?)?S(?:\. ?)?Sp\.?",  # CSSp
				"C(?:\. ?)?Ss(?:\. ?)?(?:CC|Cc|R)\.?",  # CSsCC, CSsR
				"C(?:\. ?)?S(?:\. ?)?T(?:\. ?)?F\.?",  # CSTF
				"D(?:\. ?)?K(?:\. ?)?L\.?",  # DKL
				"D(?:\. ?)?N(?:\. ?)?S\.?",  # DNS
				"F(?:\. ?)?D(?:\. ?)?C\.?",  # FDC
				"F(?:\. ?)?M(?:\. ?)?A\.?",  # FMA
				"F(?:\. ?)?M(?:\. ?)?C(?:\. ?)?S\.?",  # FMCS
				"F(?:\. ?)?M(?:\. ?)?D(?:\. ?)?D\.?",  # FMDD
				"F(?:\. ?)?S(?:\. ?)?C(?:\. ?)?I\.?",  # FSCI
				"F(?:\. ?)?S(?:\. ?)?P\.?",  # FSP
				"I(?:\. ?)?B(?:\. ?)?M(?:\. ?)?V\.?",  # IBMV
				"Inst(?:\. ?)?Char\.?",  # Inst. Char.
				"I(?:\. ?)?Sch\.?",  # ISch
				"I(?:\. ?)?S(?:\. ?)?P(?:\. ?)?X\.?",  # ISPX
				"I(?:\. ?)?S(?:\. ?)?S(?:\. ?)?M\.?",  # ISSM
				"K(?:\. ?)?M(?:\. ?)?B(?:\. ?)?M\.?",  # KMBM
				"K(?:\. ?)?S(?:\. ?)?H\.?",  # KSH
				"K(?:\. ?)?S(?:\. ?)?N(?:\. ?)?S\.?",  # KSNS
				"(?:L|M|O|S)(?:\. ?)?C\.?",  # LC, MC, OC, SC
				"M(?:\. ?)?I(?:\. ?)?C\.?",  # MIC
				"N(?:\. ?)?Id\.?",  # MId
				"M(?:\. ?)?S\.?(?: ?(?:C|J)\.?)?",  # MS, MSC, MSJ
				"N(?:\. ?)?D\.?",  # ND
				"O(?:\. ?)?(?:Camald|Carm|Cart|Cist|Cr|Crucig|F|H|M|Melit|Merced|P|Praed|Praem|T|Trinit)\.?",  # OCamald, OCarm, OCart, OCist, OCr, OCrucig, OF, OH, OM, OMelit, OMerced, OP, OPraed, OPraem, OT, OTrinit
				"O(?:\. ?)?C(?:\. ?)?(?:C|D|R)\.?",  # OCC, OCD, OCR
				"O(?:\. ?)?C(?:\. ?)?S(?:\. ?)?O\.?",  # OCSO
				"O(?:\. ?)?F(?:\. ?)?M\.?(?: ?(?:Cap|Conv|Rec)\.?)?",  # OFM, OFM Cap., OFM Conv., OFM Rec.
				"O(?:\. ?)?M(\. ?)?(?:C|I)\.?",  # OMC, OMI
				"O(?:\. ?)?(?:F(\. ?)?)?M(\. ?)?Cap\.?",  # OM Cap. OFM Cap.
				"O(?:\. ?)?S(?:\. ?)?(?:A|B|C|E|F|H|M|U)\.?",  # OSA, OSB, OSC, OSE, OSF, OSH, OSM, OSU
				"O(?:\. ?)?S(?:\. ?)?B(\. ?)?M\.?",  # OSBM
				"O(?:\. ?)?S(?:\. ?)?C(\. ?)?(?:Cap|O)\.?",  # OSC Cap., OSCO
				"O(?:\. ?)?S(?:\. ?)?F(?:\. ?)?(?:C|S)\.?",  # OSFC, OSFS
				"O(?:\. ?)?S(?:\. ?)?F(\. ?)?Gr\.?",  # OSFGr
				"O(?:\. ?)?Ss(?:\. ?)?C\.?",  # OSsC
				"O(?:\. ?)?V(?:\. ?)?M\.?",  # OVM
				"P(?:\. ?)?D(?:\. ?)?D(\. ?)?M\.?",  # PDDM
				"P(?:\. ?)?O\.?",  # PO
				"P(?:\. ?)?S(?:\. ?)?(?:M|S)\.?",  # PSM, PSS
				"R(?:\. ?)?G(?:\. ?)?S\.?",  # RGS
				"S(?:\. ?)?(?:A|J|S)(?:\. ?)?C\.?",  # SAC, SJC, SSC
				"S(?:\. ?)?C(?:\. ?)?(?:B|H|M)\.?",  # SCB, SCH, SCM
				"S(?:\. ?)?C(?:\. ?)?S(\. ?)?C\.?",  # SCSC
				"S(?:\. ?)?D(?:\. ?)?(?:B|J|S)\.?",  # SDB, SDJ, SDS
				"Sch(?:\. ?)?P\.?",  # SchP
				"(?:S|T)(?:\. ?)?(?:I|J)\.?",  # SI, SJ, TI, TJ
				"S(?:\. ?)?(?:P(?:\. ?)?)?M\.?",  # SM, SPM
				"S(?:\. ?)?M(?:\. ?)?F(?:\. ?)?O\.?",  # SMFO
				"S(?:\. ?)?M(?:\. ?)?O(?:\. ?)?M\.?",  # SMOM
				"S(?:\. ?)?(?:P|Praem)\.?",  # SP, SPraem
				"S(?:\. ?)?S(?:\. ?)?J\.?",  # SSJ
				"S(?:\. ?)?S(?:\. ?)?N(?:\. ?)?D\.?",  # SSND
				"S(?:\. ?)?(?:S|T)(?:\. ?)?S\.?",  # SSS, STS
				"S(?:\. ?)?V\.?(?: ?D\.?)?",  # SV, SVD
			]
		# u titulů bez teček je třeba kontrolova mezeru, čárku nebo konec (například MA jinak vezme následující příjmení začínající "Ma..." a bude toto jméno považovat za součást předchozího)
		re_titles_civil = [
			r"J[rn]\.?",
			"Sr\.?",
			"ml(?:\.|adší)?",
			"st(?:\.|arší)?",
			"jun(\.|ior)?",
			"[PT]h(\.\s?)?D\.?",
			"MBA",
			"M\.?A\.?",
			"M\.?S\.?",
			"M\.?Sc\.?",
			"CSc\.",
			"D(?:\.|r\.?)Sc\.",
			"[Dd]r\. ?h\. ?c\.",
			"DiS\.",
			"CC",
		]
		#                 v---- need to be space without asterisk - with asterisk the comma will be replaced
		alias = re.sub(
			r", (?!("
			+ "|".join(re_titles_civil + re_titles_religious)
			+ r")(\.|,| |$))",
			"|",
			alias,
			flags=re.I,
		)
		alias = regex.sub(
		    r"(?<=^|\|)\p{Lu}\.(?:\s*\p{Lu}\.)+(\||$)", "\g<1>", alias
		)  # Elimination of initials like "V. H." (also in infobox pseudonymes, nicknames, ...)

		return alias

	##
	# @brief Zpracuje a konvertuje datum narození/úmrtí osoby do jednotného formátu.
	# @param date - datum narození/úmrtí osoby (str)
	# @param is_birth - určuje, zda se jedná o datum narození, či úmrtí (bool)
	# @return Datum narození/úmrtí osoby v jednotném formátu. (str)
	@classmethod
	def _convert_date(cls, date, is_birth):
		# detekce př. n. l.
		date_bc = True if re.search(r"př\.?\s*n\.?\s*l\.?", date, re.I) else False

		# datum před úpravou
		orig_date = date[:]

		# odstranění přebytečného textu
		date = date.replace("?", "").replace("~", "")
		date = re.sub(r"{{(?!\s*datum|\s*julgreg)[^}]+}}", "", date, flags=re.I)
		date = re.sub(r"př\.\s*n\.\s*l\.", "", date, flags=re.I)

		# staletí - začátek
		date = cls._subx(
			r".*?(\d+\.?|prvn.|druh.)\s*(?:pol(?:\.|ovin.))\s*(\d+)\.?\s*(?:st(?:\.?|ol\.?|oletí)).*",
			lambda x: cls._regex_date(x, 0),
			date,
			flags=re.I,
		)

		date = cls._subx(
			r".*?(\d+)\.?\s*(?:až?|[\-–—−/])\s*(\d+)\.?\s*(?:st\.?|stol\.?|století).*",
			lambda x: cls._regex_date(x, 1),
			date,
			flags=re.I,
		)

		date = cls._subx(
			r".*?(\d+)\.?\s*(?:st\.?|stol\.?|století).*",
			lambda x: cls._regex_date(x, 2),
			date,
			flags=re.I,
		)
		# staletí - konec

		# data z šablon - začátek
		if is_birth:
			date = cls._subx(
				r".*?{{\s*datum[\s_]+narození\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*",
				lambda x: cls._regex_date(x, 3),
				date,
				flags=re.I,
			)
		else:
			date = cls._subx(
				r".*?{{\s*datum[\s_]+úmrtí\D*\|\s*(\d*)\s*\|\s*(\d*)\s*\|\s*(\d*)[^}]*}}.*",
				lambda x: cls._regex_date(x, 3),
				date,
				flags=re.I,
			)
		date = cls._subx(
			r".*?{{\s*JULGREGDATUM\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)[^}]*}}.*",
			lambda x: cls._regex_date(x, 4),
			date,
			flags=re.I,
		)
		# data z šablon - konec

		# data napsaná natvrdo - začátek
		date = cls._subx(
			r".*?(\d+)\.\s*((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+)(?:\s*,)?\s+(\d+).*",
			lambda x: cls._regex_date(x, 8),
			date,
			flags=re.I,
		)
		date = cls._subx(
			r".*?(\d+)\s*(?:či|až?|nebo|[\-–—−/])\s*(\d+).*",
			lambda x: cls._regex_date(x, 5),
			date,
			flags=re.I,
		)
		date = cls._subx(
			r".*?(\d+)\s*\.\s*(\d+)\s*\.\s*(\d+).*",
			lambda x: cls._regex_date(x, 4),
			date,
		)
		date = cls._subx(
			r".*?((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+)(?:\s*,)?\s+(\d+).*",
			lambda x: cls._regex_date(x, 9),
			date,
			flags=re.I,
		)
		date = cls._subx(
			r".*?(\d+)\.\s*((?:led|úno|bře|dub|kvě|čer|srp|zář|říj|list|pros)[^\W\d_]+).*",
			lambda x: cls._regex_date(x, 7),
			date,
			flags=re.I,
		)
		date = cls._subx(r".*?(\d{1,4}).*", lambda x: cls._regex_date(x, 6), date)
		# data napsaná natvrdo - konec

		# odstranění zdvojených bílých znaků a jejich převod na mezery
		date = cls._subx(r"\s+", " ", date).strip()

		# odstranění nezkonvertovatelných dat
		date = "" if orig_date == date else date

		# převod na formát data před naším letopočtem - začátek
		if date and date_bc:
			rexp = re.search(r"^([\d?]{4})-([\d?]{2})-([\d?]{2})$", date)
			if rexp and rexp.group(1):
				if rexp.group(1) != "????":
					bc_year = (
						"-" + str(int(rexp.group(1)) - 1).zfill(4)
						if rexp.group(1) != "0001"
						else "0000"
					)
					date = "{}-{}-{}".format(bc_year, rexp.group(2), rexp.group(3))
			else:
				rexp = re.search(
					r"^([\d?]{4})-([\d?]{2})-([\d?]{2})/([\d?]{4})-([\d?]{2})-([\d?]{2})$",
					date,
				)
				if rexp and rexp.group(1) and rexp.group(4):
					if rexp.group(1) != "????" and rexp.group(4) != "????":
						yr1, yr2 = int(rexp.group(1)), int(rexp.group(4))
						if (
							yr1 < yr2
						):  # prohození hodnot, pokud je první rok menší než druhý
							yr1, yr2 = yr2, yr1
						bc_year1 = "-" + str(yr1 - 1).zfill(4) if yr1 != 1 else "0000"
						bc_year2 = "-" + str(yr2 - 1).zfill(4) if yr2 != 1 else "0000"
						date = "{}-{}-{}/{}-{}-{}".format(
							bc_year1,
							rexp.group(2),
							rexp.group(3),
							bc_year2,
							rexp.group(6),
							rexp.group(6),
						)
		# převod na formát data před naším letopočtem - konec

		return date

	##
	# @brief Převádí předaný match object na jednotný formát data dle standardu ISO 8601.
	# @param match_obj  - match object (MatchObject)
	# @param match_type - určuje, jaký typ formátu se má aplikovat (int)
	# @return Jednotný formát data. (str)
	@classmethod
	def _regex_date(cls, match_obj, match_type):
		
		if match_type == 0:
			f = "{:04d}-??-??/{:04d}-??-??"
			if re.search(r"1\.?|prvn.", match_obj.group(1), re.I):
				f = f.format(
					(int(match_obj.group(2)) - 1) * 100 + 1,
					int(match_obj.group(2)) * 100 - 50,
				)
			else:
				f = f.format(
					(int(match_obj.group(2)) - 1) * 100 + 51,
					int(match_obj.group(2)) * 100,
				)
			return f

		if match_type == 1:
			f = "{:04d}-??-??/{:04d}-??-??"
			return f.format(
				(int(match_obj.group(1)) - 1) * 100 + 1, int(match_obj.group(2)) * 100
			)

		if match_type == 2:
			f = "{:04d}-??-??/{:04d}-??-??"
			return f.format(
				(int(match_obj.group(1)) - 1) * 100 + 1, int(match_obj.group(1)) * 100
			)

		if match_type == 3:
			f = "{}-{}-{}"
			year = "????" if not match_obj.group(1) else match_obj.group(1).zfill(4)
			month = "??" if not match_obj.group(2) else match_obj.group(2).zfill(2)
			day = "??" if not match_obj.group(3) else match_obj.group(3).zfill(2)
			return f.format(year, month, day)

		if match_type == 4:
			f = "{}-{}-{}"
			return f.format(
				match_obj.group(3).zfill(4),
				match_obj.group(2).zfill(2),
				match_obj.group(1).zfill(2),
			)

		if match_type == 5:
			return "{}-??-??/{}-??-??".format(
				match_obj.group(1).zfill(4), match_obj.group(2).zfill(4)
			)

		if match_type == 6:
			return "{}-??-??".format(match_obj.group(1).zfill(4))

		if match_type == 7:
			f = "????-{}-{}"
			return f.format(
				cls._get_cal_month(match_obj.group(2)), match_obj.group(1).zfill(2)
			)

		if match_type == 8:
			f = "{}-{}-{}"
			return f.format(
				match_obj.group(3).zfill(4),
				cls._get_cal_month(match_obj.group(2)),
				match_obj.group(1).zfill(2),
			)

		if match_type == 9:
			f = "{}-{}-??"
			return f.format(
				match_obj.group(2).zfill(4), cls._get_cal_month(match_obj.group(1))
			)

	##
	# @brief Převádí název kalendářního měsíce na číselný tvar.
	# @param month - název měsíce (str)
	# @return Číslo kalendářního měsíce na 2 pozicích, jinak ??. (str)
	@staticmethod
	def _get_cal_month(month):
		cal_months_part = [
			"led",
			"únor",
			"břez",
			"dub",
			"květ",
			"červ",
			"červen",
			"srp",
			"září",
			"říj",
			"listopad",
			"prosin",
		]

		for idx, mon in enumerate(cal_months_part, 1):
			if mon in month.lower():
				if (
					idx == 6 and "c" in month
				):  # v případě špatné identifikace června a července v některých pádech
					return "07"
				return str(idx).zfill(2)

		return "??"

	##
	# @brief Vykonává totožný úkon jako funkce sub z modulu re, ale jen v případě, že nenarazí na datum ve standardizovaném formátu.
	# @param pattern - vzor (str)
	# @param repl - náhrada (str)
	# @param string - řetězec, na kterém má být úkon proveden (str)
	# @param count - počet výskytů, na kterých má být úkon proveden (int)
	# @param flags - speciální značky, které ovlivňují chování funkce (int)
	@staticmethod
	def _subx(pattern, repl, string, count=0, flags=0):		
		if re.match(r"[\d?]+-[\d?]+-[\d?]+", string):
			return string
		return re.sub(pattern, repl, string, count, flags)
