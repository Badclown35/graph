#!/usr/bin/env python3
"""Build the offline Android achievement catalogue from Graph's source definitions."""
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "achievement"
ASSET_ROOT = ROOT / "android" / "app" / "src" / "main" / "assets"
IMAGE_SOURCE = ROOT / "public_html" / "image" / "achievement"
IMAGE_DEST = ASSET_ROOT / "achievement"

# The mobile catalogue intentionally omits explicitly adult/sexual achievement groups.
EXCLUDED = {
    "anime-boku-no-pico.json",
    "anime-pervert-0.json", "anime-pervert-1.json",
    "anime-pervert-2.json", "anime-pervert-3.json",
    "manga-pervert-0.json", "manga-pervert-1.json",
    "manga-pervert-2.json", "manga-pervert-3.json",
    "manga-yaoi-shounen-ai.json", "manga-yuri-shoujo-ai.json",
}

GENRES = {
    1:"Action", 2:"Adventure", 4:"Comedy", 5:"Avant Garde", 6:"Mythology",
    7:"Mystery", 8:"Drama", 9:"Ecchi", 10:"Fantasy", 11:"Strategy Game",
    13:"Historical", 14:"Horror", 15:"Kids", 16:"Martial Arts", 17:"Mecha",
    18:"Music", 19:"Parody", 20:"Samurai", 21:"Shoujo", 22:"Romance",
    23:"School", 24:"Sci-Fi", 25:"Shounen", 26:"Shoujo Ai", 27:"Shounen Ai",
    28:"Slice of Life", 29:"Space", 30:"Sports", 31:"Super Power",
    32:"Vampire", 36:"Gourmet", 37:"Hentai", 38:"Suspense", 39:"Award Winning",
    40:"Gourmet", 41:"Work Life", 42:"Josei", 43:"Mature", 46:"Award Winning",
    47:"Gourmet", 48:"Work Life", 49:"Erotica", 50:"Adult Cast",
    51:"Anthropomorphic", 52:"CGDCT", 53:"Childcare", 54:"Combat Sports",
    55:"Crossdressing", 56:"Delinquents", 57:"Educational", 58:"Gag Humor",
    59:"Gore", 60:"High Stakes Game", 61:"Idols", 62:"Isekai",
    63:"Iyashikei", 64:"Love Polygon", 65:"Magical Sex Shift", 66:"Medical",
    67:"Organized Crime", 68:"Otaku Culture", 69:"Performing Arts",
    70:"Pets", 71:"Reincarnation", 72:"Showbiz", 73:"Video Game",
    74:"Time Travel", 75:"Visual Arts", 76:"Theatre",
}

def friendly_name(filename):
    slug = filename[:-5]
    slug = re.sub(r"^(anime|manga)-", "", slug)
    names = {
        "dementia-psychological":"Psychological", "finished":"Completed entries", "dropped-0":"Never dropped",
        "duration-short":"Short episodes", "episode-long":"Long series",
        "franchise-long":"Franchise completion", "game":"Video game adaptations",
        "gar":"GAR", "historical":"Historical", "horror-thriller":"Horror / Thriller",
        "light-novel":"Light novel adaptations", "mahou-shoujo":"Magical girls",
        "mecha":"Mecha", "music":"Music", "mystery":"Mystery", "original":"Original source",
        "release-classic":"Classic releases", "release-old":"Old releases",
        "romance":"Romance", "school-days":"School Days", "score-high":"High average score",
        "score-low":"Low average score", "score-very-low":"Very low average score",
        "slice-of-life":"Slice of Life", "space":"Space", "sports":"Sports",
        "studio-ghibli":"Studio Ghibli", "time":"Total watch/read time",
        "year":"Release-year variety", "horror":"Horror", "novel":"Novels",
        "vampire-demons":"Vampires / Demons", "volume-long":"Long manga",
        "re":"Rewatches",
    }
    return names.get(slug, slug.replace("-", " ").title())

def how_to_earn(requirement, media, group_name):
    kind = requirement.get("type", "unknown")
    verb = "complete" if media == "A" else "finish reading"
    unit = "anime entries" if media == "A" else "manga entries"
    if kind == "finished":
        return f"{verb.capitalize()} the required number of {unit}."
    if kind == "dropped-0":
        return f"{verb.capitalize()} entries without dropping any. One dropped entry disables this badge."
    if kind == "genre-title":
        return f"{verb.capitalize()} {group_name.lower()} titles. The count uses completed entries and any extra titles specified by the original definition."
    if kind == "title":
        return f"{verb.capitalize()} the specific titles listed for this achievement."
    if kind == "source-title":
        return f"{verb.capitalize()} entries with the required source type, or the specific listed titles."
    if kind == "score":
        return "Reach the required average score across eligible non-planned entries."
    if kind == "release-old":
        return "Complete entries whose release ended before 1981."
    if kind == "release-classic":
        return "Complete entries whose release ended from 1981 through 2000."
    if kind == "duration-short":
        return "Complete entries with an episode runtime under 16 minutes."
    if kind == "episode-long":
        return "Have more than 99 watched episodes on an eligible entry."
    if kind == "volume-long":
        return "Read more than 19 volumes of an eligible manga."
    if kind == "franchise":
        return "Complete at least two entries in a franchise with more than 199 combined episodes."
    if kind == "novel":
        return "Read volumes from manga classified as a novel or light novel."
    if kind == "time":
        return "Accumulate the required total watch/read time."
    if kind == "re":
        return "Accumulate the required number of rewatches."
    if kind == "year":
        return "Complete entries spanning the required number of distinct release years."
    return f"Meet the {group_name.lower()} requirement shown for this badge."

catalog = {"schemaVersion":1, "source":"Graph achievement definitions", "groups":[]}
for path in sorted(SOURCE.glob("*.json")):
    if path.name in EXCLUDED:
        continue
    raw_definition = path.read_text(encoding="utf-8")
    raw_definition = re.sub(r"//.*$", "", raw_definition, flags=re.MULTILINE)
    raw_definition = re.sub(r"#.*$", "", raw_definition, flags=re.MULTILINE)
    definition = json.loads(raw_definition)
    media = "anime" if definition.get("media") == "A" else "manga"
    group_name = friendly_name(path.name)
    requirement = definition.get("requirement", {})
    group = {
        "id": path.stem,
        "name": group_name,
        "media": media,
        "requirementType": requirement.get("type", "unknown"),
        "howToEarn": how_to_earn(requirement, media, group_name),
        "achievements": []
    }
    for achievement in definition.get("achievements", []):
        badge_id = achievement.get("id", "")
        matches = sorted(IMAGE_SOURCE.glob(badge_id + ".*"))
        image = matches[0].name if matches else ""
        group["achievements"].append({
            "id": badge_id,
            "level": achievement.get("level", ""),
            "title": achievement.get("title", ""),
            "description": achievement.get("desc", ""),
            "threshold": achievement.get("threshold", ""),
            "image": image,
            "howToEarn": how_to_earn(requirement, media, group_name)
        })
    if group["achievements"]:
        catalog["groups"].append(group)

ASSET_ROOT.mkdir(parents=True, exist_ok=True)
IMAGE_DEST.mkdir(parents=True, exist_ok=True)
(ASSET_ROOT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
(ASSET_ROOT / "catalog.js").write_text("window.GRAPH_CATALOG = " + json.dumps(catalog, ensure_ascii=False) + ";", encoding="utf-8")
for item in IMAGE_SOURCE.iterdir():
    if item.is_file():
        shutil.copy2(item, IMAGE_DEST / item.name)
print(f"Built {sum(len(g['achievements']) for g in catalog['groups'])} badges in {len(catalog['groups'])} groups.")
