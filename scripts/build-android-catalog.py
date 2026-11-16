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

# Keep only categories that are explicitly adult/sexual out of this teen-friendly edition.
# Boys Love / Girls Love are ordinary romance-genre categories and are included.

EXCLUDED = {
    
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
    slug = re.sub(r"^(anime|manga)-", "", filename[:-5])
    names = {
        "dementia-psychological":"Psychological", "finished":"Completed entries",
        "dropped-0":"Never dropped", "duration-short":"Short episodes",
        "episode-long":"Long series", "franchise-long":"Franchise completion",
        "game":"Video game adaptations", "gar":"GAR", "historical":"Historical",
        "horror-thriller":"Horror / Thriller", "light-novel":"Light novel adaptations",
        "mahou-shoujo":"Magical girls", "mecha":"Mecha", "music":"Music",
        "mystery":"Mystery", "original":"Original source",
        "release-classic":"Classic releases", "release-old":"Old releases",
        "romance":"Romance", "school-days":"School Days",
        "score-high":"High average score", "score-low":"Low average score",
        "score-very-low":"Very low average score", "slice-of-life":"Slice of Life",
        "space":"Space", "sports":"Sports", "studio-ghibli":"Studio Ghibli",
        "time":"Total watch/read time", "year":"Release-year variety",
        "horror":"Horror", "novel":"Novels", "vampire-demons":"Vampires / Demons",
        "volume-long":"Long manga", "re":"Rewatches / rereads",
        "yaoi-shounen-ai":"Boys Love", "yuri-shoujo-ai":"Girls Love",
    }
    return names.get(slug, slug.replace("-", " ").title())

def threshold_label(threshold, kind, media):
    unit = "completed anime entries" if media == "anime" else "completed manga entries"
    if kind == "score":
        return "Average MAL score: " + str(threshold) + " (out of 10)"
    if kind == "episode-long":
        return str(threshold) + " qualifying anime entries with over 99 watched episodes"
    if kind == "volume-long":
        return str(threshold) + " qualifying manga entries with over 19 read volumes"
    if kind == "re":
        return str(threshold) + " total rewatches/rereads"
    if kind == "time":
        return str(threshold) + " total watch/read time (Graph's original time calculation)"
    if kind == "year":
        return str(threshold) + " distinct release years"
    if kind == "franchise":
        return str(threshold) + " qualifying franchise completions"
    return str(threshold) + " " + unit + " matching this badge group"

def how_to_earn(requirement, media, group_name):
    kind = requirement.get("type", "unknown")
    unit = "anime entries" if media == "anime" else "manga entries"
    verb = "complete" if media == "anime" else "finish reading"
    if kind == "finished":
        return f"Import your MAL list, then {verb} the number of {unit} shown on the level. Each separate MAL entry counts separately."
    if kind == "dropped-0":
        return f"{verb.capitalize()} the required number of {unit} while keeping your Dropped count at zero. Even one dropped entry blocks this group."
    if kind == "genre-title":
        genre_id = requirement.get("genre")
        genre_names = {40:"Psychological", 13:"Historical", 14:"Horror", 22:"Romance", 28:"Slice of Life", 10:"Fantasy", 7:"Mystery", 24:"Sci-Fi", 30:"Sports", 18:"Music", 17:"Mecha", 32:"Vampire", 2:"Adventure", 1:"Action", 4:"Comedy", 8:"Drama"}
        genre = genre_names.get(genre_id, group_name)
        titles = requirement.get("titles", [])
        if genre_id is not None and titles:
            return f"Finish {unit} tagged {genre} (MAL genre ID {genre_id}), OR finish the extra titles in Graph's original rule. On MAL, open each title and check its Genres/Theme tags. Only entries marked Completed count; reach the target shown on this level."
        if genre_id is not None:
            return f"Finish {unit} tagged {genre} (MAL genre ID {genre_id}). On MAL, open each title and check its Genres/Theme tags; only entries marked Completed count. Reach the target shown on this level."
        if titles:
            return f"Finish the exact titles included in Graph's original rule. Match them by MAL ID in the source definition; only Completed entries count. Reach the target shown on this level."
        return f"Finish entries matching the {group_name} rule. Only Completed entries count; reach the target shown on this level."
    if kind == "title":
        return f"{verb.capitalize()} the exact MAL title(s) listed in Graph's original definition. Similar titles or another season do not count unless separately listed."
    if kind == "source-title":
        source_ids = requirement.get("source", [])
        if isinstance(source_ids, int):
            source_ids = [source_ids]
        source_names = {1:"Original",2:"Manga",3:"4-koma manga",4:"Web manga",5:"Digital manga",6:"Novel",7:"Light novel",8:"Visual novel",9:"Game",10:"Music",11:"Picture book",12:"Other"}
        sources = ", ".join(source_names.get(x, f"source ID {x}") for x in source_ids) or "the source type stated by Graph"
        return f"Finish {unit} whose MAL Source field is {sources}. Open the title's MAL page and check Information → Source. Only Completed entries count; reach the target shown on this level."
    if kind == "score":
        return "Reach the average MAL score range printed on the level. The import calculates the mean of scored entries and ignores planned entries and unscored entries."
    if kind == "release-old":
        return "Complete entries whose release ended before 1981. The year comes from Graph's title metadata, not the date you watched it."
    if kind == "release-classic":
        return "Complete entries whose release ended from 1981 through 2000. The year comes from Graph's title metadata."
    if kind == "duration-short":
        return "Complete anime entries with an episode runtime under 16 minutes. Runtime is read from Graph's title metadata."
    if kind == "episode-long":
        return "Have the required number of eligible anime entries with more than 99 watched episodes on each entry."
    if kind == "volume-long":
        return "Have the required number of manga entries with more than 19 volumes read on each entry. Your MAL export must include read-volume progress."
    if kind == "franchise":
        return "Complete at least two entries in a franchise whose combined episode count is over 199. Franchise and episode data come from Graph's metadata."
    if kind == "novel":
        return "Finish reading entries Graph classifies as novels or light novels. The classification comes from Graph's manga metadata."
    if kind == "time":
        return "Accumulate the required total watch/read time. Graph calculates this from its title metadata and your list progress."
    if kind == "re":
        return "Accumulate the total number of rewatches or rereads shown on the level. Import the MAL rewatch/reread count."
    if kind == "year":
        return "Complete entries spanning the required number of distinct release years. Release years come from Graph's title metadata."
    return f"Follow the target shown on the card and Graph's original {group_name.lower()} rule."

catalog = {"schemaVersion":2, "source":"Graph achievement definitions", "groups":[]}
for path in sorted(SOURCE.glob("*.json")):
    if path.name in EXCLUDED:
        continue
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"//.*$", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"#.*$", "", raw, flags=re.MULTILINE)
    definition = json.loads(raw)
    media = "anime" if definition.get("media") == "A" else "manga"
    group_name = friendly_name(path.name)
    requirement = definition.get("requirement", {})
    kind = requirement.get("type", "unknown")
    group_how = how_to_earn(requirement, media, group_name)
    group = {
        "id": path.stem, "name": group_name, "media": media,
        "requirementType": kind, "howToEarn": group_how, "achievements": []
    }
    for achievement in definition.get("achievements", []):
        badge_id = achievement.get("id", "")
        matches = sorted(IMAGE_SOURCE.glob(badge_id + ".*"))
        image = matches[0].name if matches else ""
        group["achievements"].append({
            "id": badge_id, "level": achievement.get("level", ""),
            "title": achievement.get("title", ""),
            "description": achievement.get("desc", ""),
            "threshold": achievement.get("threshold", ""),
            "thresholdLabel": threshold_label(achievement.get("threshold", ""), kind, media),
            "image": image, "howToEarn": group_how
        })
    if group["achievements"]:
        catalog["groups"].append(group)

ASSET_ROOT.mkdir(parents=True, exist_ok=True)
IMAGE_DEST.mkdir(parents=True, exist_ok=True)
(ASSET_ROOT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
(ASSET_ROOT / "catalog.js").write_text("window.GRAPH_CATALOG = " + json.dumps(catalog, ensure_ascii=False) + ";", encoding="utf-8")
used_images = {a["image"] for g in catalog["groups"] for a in g["achievements"] if a["image"]}
for item in IMAGE_SOURCE.iterdir():
    if item.is_file() and item.name in used_images:
        shutil.copy2(item, IMAGE_DEST / item.name)
print(f"Built {sum(len(g['achievements']) for g in catalog['groups'])} badges in {len(catalog['groups'])} groups.")
