
import re
from lang_modules.cs.core_utils import CoreUtils

class SettlementUtils:

	KEYWORDS = {
		"population": ["počet obyvatel", "počet_obyvatel", "pocet obyvatel", "pocet_obyvatel"],
		"country": ["země", "stát"]
	}
