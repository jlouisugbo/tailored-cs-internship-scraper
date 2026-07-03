import re

US_STATE_ABBREVIATIONS = frozenset({
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
})

US_MARKERS = frozenset({
    "united states", "usa", "u.s.", "u.s.a.", "us",
})

# Closed, well-defined set (world country names) rather than an ad-hoc list
# of examples -- postings from global companies use "<Country> - <City>"
# formats for every country on earth, so enumerating cities never keeps up.
NON_US_COUNTRIES = frozenset({
    "afghanistan", "albania", "algeria", "andorra", "angola", "argentina",
    "armenia", "australia", "austria", "azerbaijan", "bahamas", "bahrain",
    "bangladesh", "barbados", "belarus", "belgium", "belize", "benin",
    "bhutan", "bolivia", "bosnia", "botswana", "brazil", "brunei",
    "bulgaria", "burkina faso", "burundi", "cambodia", "cameroon", "canada",
    "chad", "chile", "china", "colombia", "congo", "costa rica", "croatia",
    "cuba", "cyprus", "czechia", "czech republic", "denmark", "djibouti",
    "dominican republic", "ecuador", "egypt", "el salvador", "england",
    "estonia", "eswatini", "ethiopia", "fiji", "finland", "france", "gabon",
    "gambia", "germany", "ghana", "greece", "guatemala",
    "guinea", "guyana", "haiti", "honduras", "hong kong", "hungary",
    "iceland", "india", "indonesia", "iran", "iraq", "ireland", "israel",
    "italy", "jamaica", "japan", "jordan", "kazakhstan", "kenya", "kosovo",
    "kuwait", "kyrgyzstan", "laos", "latvia", "lebanon", "lesotho",
    "liberia", "libya", "liechtenstein", "lithuania", "luxembourg",
    "madagascar", "malawi", "malaysia", "maldives", "mali", "malta",
    "mauritania", "mauritius", "mexico", "moldova", "monaco", "mongolia",
    "montenegro", "morocco", "mozambique", "myanmar", "namibia", "nepal",
    "netherlands", "new zealand", "nicaragua", "niger", "nigeria",
    "north macedonia", "norway", "oman", "pakistan", "panama",
    "papua new guinea", "paraguay", "peru", "philippines", "poland",
    "portugal", "qatar", "romania", "russia", "rwanda", "saudi arabia",
    "scotland", "senegal", "serbia", "sierra leone", "singapore",
    "slovakia", "slovenia", "somalia", "south africa", "south korea",
    "spain", "sri lanka", "sudan", "suriname", "sweden", "switzerland",
    "syria", "taiwan", "tajikistan", "tanzania", "thailand", "togo",
    "trinidad", "tunisia", "turkey", "turkmenistan", "uganda", "ukraine",
    "united arab emirates", "united kingdom", "uruguay", "uzbekistan",
    "venezuela", "vietnam", "wales", "yemen", "zambia", "zimbabwe",
})

# Cities that show up without a country suffix often enough to be worth a
# direct match (e.g. "London" alone rather than "London, United Kingdom").
NON_US_CITIES = frozenset({
    "london", "dublin", "manchester", "edinburgh",
    "toronto", "vancouver", "montreal",
    "bangalore", "bengaluru", "hyderabad", "mumbai", "pune", "delhi",
    "gurgaon", "gurugram", "chennai", "noida",
    "berlin", "munich", "paris", "sydney", "melbourne",
    "beijing", "shanghai", "shenzhen", "tokyo", "sao paulo", "mexico city",
    "buenos aires", "bogota", "santiago", "lima", "montevideo", "quito",
    "madrid", "barcelona", "amsterdam", "warsaw", "tel aviv", "zurich",
    "stockholm",
})

NON_US_MARKERS = NON_US_COUNTRIES | NON_US_CITIES | frozenset({"uk", "emea", "apac", "latam", "international"})

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SEGMENT_SPLIT_RE = re.compile(r"</?br\s*/?>", re.IGNORECASE)
_STATE_ABBR_RE = re.compile(r"\b[A-Z]{2}\b")


def _has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def _segment_is_us(segment: str) -> bool | None:
    """Classify one location segment. None means no clear US/non-US signal."""
    text = segment.strip().lower()
    if not text:
        return None
    if any(_has_word(text, marker) for marker in US_MARKERS):
        return True
    if any(_has_word(text, marker) for marker in NON_US_MARKERS):
        return False
    for abbr in _STATE_ABBR_RE.findall(segment):
        if abbr in US_STATE_ABBREVIATIONS:
            return True
    return None


def is_us_location(location: str) -> bool:
    """US if any segment matches; ambiguous (blank/"Remote"/no signal) defaults True."""
    if not location:
        return True
    raw_segments = _SEGMENT_SPLIT_RE.split(location)
    segments = [_HTML_TAG_RE.sub(" ", segment) for segment in raw_segments]
    results = [_segment_is_us(segment) for segment in segments]
    if any(result is True for result in results):
        return True
    if any(result is False for result in results):
        return False
    return True
