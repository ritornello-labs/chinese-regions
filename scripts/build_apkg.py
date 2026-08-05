#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
from pathlib import Path

import genanki


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTES_CSV = REPO_ROOT / "data/raw/china_regions_notes_seed.csv"
OUTPUT_APKG = REPO_ROOT / "out/chinese-regions.apkg"
MEDIA_DIR = REPO_ROOT / "media/regions"
MODEL_ID = 1_893_420_011
DECK_ID = 1_893_420_012
MODEL_SCHEMA_VERSION = 3

BLANK_MAP_FILENAME = "china_blank_map.svg"

LOCATOR_URL_TO_FILENAME = {
    "https://commons.wikimedia.org/wiki/Special:FilePath/North_China.svg": "north_china_locator.svg",
    "https://commons.wikimedia.org/wiki/Special:FilePath/East_China.svg": "east_china_locator.svg",
    "https://commons.wikimedia.org/wiki/Special:FilePath/South_Central_China.svg": "south_central_china_locator.svg",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Southwest_China.svg": "southwest_china_locator.svg",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Northeast_China.svg": "northeast_china_locator.svg",
    "https://commons.wikimedia.org/wiki/Special:FilePath/Northwest_China.svg": "northwest_china_locator.svg",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def split_connection_lines(value: str) -> list[str]:
    return [piece.strip() for piece in (value or "").split("<br>") if piece.strip()]


def split_csv_like_values(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def html_member_chips(items: list[str]) -> str:
    if not items:
        return ""
    chips = "".join(f'<span class="member-chip">{html.escape(item)}</span>' for item in items)
    return f'<div class="member-chips">{chips}</div>'


def html_connection_rows(lines: list[str]) -> str:
    if not lines:
        return ""
    rows: list[str] = []
    for line in lines:
        if ":" in line:
            region, neighbors = line.split(":", 1)
            rows.append(
                '<div class="connection-row">'
                f'<div class="connection-region">{html.escape(region.strip())}</div>'
                f'<div class="connection-neighbors">{html.escape(neighbors.strip())}</div>'
                "</div>"
            )
        else:
            rows.append(f'<div class="connection-row"><div class="connection-neighbors">{html.escape(line)}</div></div>')
    return '<div class="connection-rows">' + "".join(rows) + "</div>"


def make_map_html(filename: str, alt_text: str, klass: str) -> str:
    return f'<img class="{klass}" src="{filename}" alt="{html.escape(alt_text)}">'


def required_media_paths(rows: list[dict[str, str]]) -> list[Path]:
    out: list[Path] = [MEDIA_DIR / BLANK_MAP_FILENAME]
    for row in rows:
        locator_url = (row.get("locator_map") or "").strip()
        filename = LOCATOR_URL_TO_FILENAME.get(locator_url)
        if not filename:
            continue
        out.append(MEDIA_DIR / filename)
    return sorted(dict.fromkeys(out))


def ensure_required_media(rows: list[dict[str, str]]) -> list[str]:
    required = required_media_paths(rows)
    missing = [path for path in required if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {path.relative_to(REPO_ROOT)}" for path in missing)
        raise SystemExit(
            "Missing required media files.\n"
            "Run `scripts/fetch_region_media.py` first.\n"
            f"{missing_list}"
        )
    return [str(path) for path in required]


def fieldnames_for_model() -> list[str]:
    return [
        "mandarin_name",
        "blank_map",
        "locator_map",
        "pinyin_name",
        "english_name",
        "member_provinces",
        "connections",
        "Card_Member_Chips",
        "Card_Connections_HTML",
        "Card_BlankMap_HTML",
        "Card_LocatorMap_HTML",
        "Wikipedia",
    ]


def model_css() -> str:
    return """
:root{
  --paper:#f8efe0;
  --paper-deep:#ead7b0;
  --paper-rose:#f4dfd5;
  --ink:#241512;
  --muted:#6d5246;
  --jade:#2f6a58;
  --jade-soft:#dbe9e1;
  --lacquer:#8d1424;
  --lacquer-deep:#56101a;
  --vermillion:#c52f30;
  --gold:#d5b15f;
  --gold-soft:#f5e4b2;
  --rule:rgba(97,35,23,0.22);
  --shadow:rgba(39,12,10,0.24);
}
.card{
  font-family:"Iowan Old Style","Palatino Linotype","Book Antiqua","Baskerville",serif;
  color:var(--ink);
  background:
    radial-gradient(circle at top left, rgba(213,177,95,0.18), transparent 24%),
    radial-gradient(circle at 82% 14%, rgba(197,47,48,0.16), transparent 22%),
    radial-gradient(circle at bottom right, rgba(47,106,88,0.10), transparent 26%),
    linear-gradient(135deg, #5d0d17 0%, #8d1424 13%, #f7eddc 13.2%, #f8efe0 68%, #ead8b7 100%);
  background-repeat:no-repeat;
  background-attachment:fixed;
  background-size:cover;
  box-sizing:border-box;
  min-height:100vh;
  font-size:19px;
  line-height:1.45;
  padding:24px 18px 30px;
}
.wrap{
  max-width:760px;
  margin:0 auto;
  position:relative;
}
.wrap::before,
.wrap::after{
  content:"";
  position:absolute;
  border-radius:50%;
  pointer-events:none;
  z-index:0;
}
.wrap::before{
  width:170px;
  height:170px;
  top:-34px;
  right:-28px;
  background:radial-gradient(circle, rgba(213,177,95,0.22) 0%, rgba(213,177,95,0.08) 34%, transparent 70%);
}
.wrap::after{
  width:110px;
  height:110px;
  bottom:-24px;
  left:-12px;
  background:radial-gradient(circle, rgba(47,106,88,0.18) 0%, transparent 72%);
}
.plate{
  position:relative;
  overflow:hidden;
  background:
    linear-gradient(180deg, rgba(255,250,241,0.92), rgba(248,239,224,0.88)),
    linear-gradient(135deg, rgba(244,223,213,0.55), rgba(255,255,255,0.16) 38%, rgba(213,177,95,0.20) 100%);
  border:1px solid rgba(118,40,24,0.22);
  border-radius:28px;
  padding:24px 22px 26px;
  box-shadow:0 22px 46px var(--shadow), inset 0 1px 0 rgba(255,250,241,0.76);
  backdrop-filter:blur(2px);
}
.plate::before{
  content:"";
  position:absolute;
  inset:10px;
  border:1.5px solid rgba(213,177,95,0.72);
  border-radius:20px;
  pointer-events:none;
  box-shadow:inset 0 0 0 1px rgba(141,20,36,0.10);
}
.plate::after{
  content:"";
  position:absolute;
  inset:16px;
  border-radius:16px;
  pointer-events:none;
  background:
    radial-gradient(circle at top left, rgba(141,20,36,0.08), transparent 22%),
    radial-gradient(circle at top right, rgba(141,20,36,0.08), transparent 22%),
    radial-gradient(circle at bottom left, rgba(141,20,36,0.08), transparent 22%),
    radial-gradient(circle at bottom right, rgba(141,20,36,0.08), transparent 22%),
    repeating-linear-gradient(135deg, transparent 0 15px, rgba(213,177,95,0.035) 15px 16px);
}
.plate > *{
  position:relative;
  z-index:1;
}
.eyebrow{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:6px 11px;
  border-radius:999px;
  border:1px solid rgba(213,177,95,0.68);
  background:linear-gradient(180deg, rgba(141,20,36,0.94), rgba(94,12,24,0.96));
  box-shadow:0 8px 18px rgba(87,14,20,0.18);
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  text-transform:uppercase;
  letter-spacing:0.18em;
  font-size:11px;
  color:var(--gold-soft);
  margin:0 0 14px;
}
.title,
.hanzi{
  font-family:"STKaiti","KaiTi","Songti SC","Noto Serif SC","Palatino Linotype","Book Antiqua",serif;
  color:var(--lacquer-deep);
  text-shadow:0 1px 0 rgba(255,249,238,0.72);
}
.title{
  font-size:54px;
  line-height:0.98;
  letter-spacing:-0.03em;
  margin:0;
}
.hanzi{
  font-size:76px;
  line-height:0.94;
  letter-spacing:-0.03em;
  margin:0;
}
.pinyin{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  color:var(--muted);
  font-size:19px;
  letter-spacing:0.03em;
  margin-top:10px;
}
.subtitle{
  color:var(--muted);
  font-size:17px;
  margin-top:10px;
}
.prompt{
  margin-top:18px;
  padding-top:16px;
  border-top:1px solid rgba(141,20,36,0.16);
  color:var(--muted);
  font-size:17px;
}
.answer-panel{
  position:relative;
  margin-top:20px;
  border-radius:24px;
  border:1px solid rgba(141,20,36,0.28);
  background:
    linear-gradient(180deg, rgba(255,248,239,0.90), rgba(250,234,224,0.88)),
    linear-gradient(135deg, rgba(141,20,36,0.12), rgba(213,177,95,0.16));
  padding:20px 18px 17px;
  box-shadow:0 14px 28px rgba(80,19,17,0.12), inset 0 0 0 1px rgba(213,177,95,0.34);
}
.answer-panel::before{
  content:"";
  position:absolute;
  inset:10px;
  border-radius:16px;
  border:1px solid rgba(213,177,95,0.42);
  pointer-events:none;
}
.answer-label{
  display:inline-block;
  padding:5px 10px 4px;
  border-radius:999px;
  background:linear-gradient(180deg, rgba(141,20,36,0.98), rgba(106,14,26,0.98));
  border:1px solid rgba(213,177,95,0.72);
  box-shadow:0 8px 16px rgba(87,14,20,0.16);
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  text-transform:uppercase;
  letter-spacing:0.16em;
  font-size:11px;
  color:var(--gold-soft);
  margin:0 0 10px;
}
.answer-main{
  font-size:36px;
  line-height:1.08;
  margin:0;
  color:var(--lacquer-deep);
}
.answer-sub{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  color:var(--muted);
  font-size:18px;
  margin-top:8px;
}
.rule{
  height:2px;
  background:linear-gradient(90deg, transparent, rgba(213,177,95,0.25), var(--gold), rgba(213,177,95,0.25), transparent);
  margin:18px 0;
}
.panel{
  position:relative;
  border:1px solid rgba(141,20,36,0.18);
  border-radius:20px;
  background:
    linear-gradient(180deg, rgba(255,250,243,0.78), rgba(250,238,225,0.72)),
    linear-gradient(135deg, rgba(47,106,88,0.06), rgba(213,177,95,0.12));
  padding:16px 16px 14px;
  box-shadow:inset 0 0 0 1px rgba(213,177,95,0.22);
}
.panel-title{
  display:inline-block;
  padding:4px 9px 3px;
  border-radius:999px;
  border:1px solid rgba(213,177,95,0.56);
  background:rgba(255,247,231,0.88);
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:0.12em;
  color:var(--lacquer);
  margin:0 0 10px;
}
.member-chips{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
}
.member-chip{
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  border:1px solid rgba(141,20,36,0.22);
  background:
    linear-gradient(180deg, rgba(255,249,240,0.94), rgba(244,223,213,0.68)),
    linear-gradient(135deg, rgba(47,106,88,0.12), rgba(213,177,95,0.18));
  padding:8px 12px;
  box-shadow:0 8px 14px rgba(80,19,17,0.08), inset 0 0 0 1px rgba(213,177,95,0.20);
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:14px;
  color:var(--ink);
}
.connections-layout{
  display:grid;
  grid-template-columns:1fr;
  gap:18px;
  margin-top:18px;
}
@media (min-width:760px){
  .connections-layout{
    grid-template-columns:0.95fr 1.15fr;
    align-items:start;
  }
}
.connection-rows{
  display:grid;
  gap:10px;
}
.connection-row{
  border-radius:18px;
  border:1px solid rgba(141,20,36,0.18);
  background:
    linear-gradient(180deg, rgba(255,250,243,0.84), rgba(248,239,224,0.76)),
    linear-gradient(135deg, rgba(213,177,95,0.10), rgba(255,255,255,0.06));
  padding:12px 13px;
  box-shadow:inset 0 0 0 1px rgba(213,177,95,0.18);
}
.connection-region{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:0.12em;
  color:var(--lacquer);
  margin-bottom:6px;
}
.connection-neighbors{
  font-size:16px;
  line-height:1.45;
}
.map-stack{
  display:grid;
  grid-template-columns:1fr;
  gap:18px;
  margin-top:18px;
}
@media (min-width:760px){
  .map-stack{
    grid-template-columns:1.05fr 1fr;
  }
}
.map-frame{
  position:relative;
  overflow:hidden;
  border-radius:24px;
  border:1px solid rgba(141,20,36,0.24);
  background:
    linear-gradient(180deg, rgba(255,251,245,0.96), rgba(248,239,224,0.90)),
    linear-gradient(135deg, rgba(213,177,95,0.14), rgba(47,106,88,0.08));
  padding:16px;
  box-shadow:0 18px 42px rgba(27,21,12,0.14), inset 0 0 0 1px rgba(213,177,95,0.24);
}
.map-frame::before{
  content:"";
  position:absolute;
  inset:10px;
  border-radius:16px;
  border:1px solid rgba(213,177,95,0.38);
  pointer-events:none;
}
.map-caption{
  display:inline-block;
  padding:4px 9px 3px;
  border-radius:999px;
  border:1px solid rgba(213,177,95,0.56);
  background:linear-gradient(180deg, rgba(141,20,36,0.94), rgba(106,14,26,0.94));
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  text-transform:uppercase;
  letter-spacing:0.12em;
  font-size:11px;
  color:var(--gold-soft);
  margin:0 0 12px;
}
.blank-map,
.locator-map{
  display:block;
  width:100%;
  height:auto;
  border-radius:14px;
}
.member-map-layout{
  display:grid;
  grid-template-columns:1fr;
  gap:18px;
  margin-top:18px;
}
@media (min-width:760px){
  .member-map-layout{
    grid-template-columns:1.05fr 0.95fr;
    align-items:start;
  }
}
.footer{
  margin-top:18px;
  padding-top:14px;
  border-top:1px solid rgba(141,20,36,0.14);
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:13px;
  letter-spacing:0.04em;
  color:var(--muted);
}
.wiki-panel{
  margin-top:18px;
  border:1px solid rgba(141,20,36,0.18);
  border-radius:20px;
  background:
    linear-gradient(180deg, rgba(255,250,243,0.78), rgba(250,238,225,0.72)),
    linear-gradient(135deg, rgba(47,106,88,0.06), rgba(213,177,95,0.12));
  padding:16px 16px 14px;
  box-shadow:inset 0 0 0 1px rgba(213,177,95,0.22);
}
.wiki-frame{
  display:block;
  width:100%;
  height:420px;
  border:1px solid rgba(141,20,36,0.16);
  border-radius:16px;
  background:rgba(255,250,243,0.92);
}
.wiki-link{
  display:inline-block;
  margin-top:10px;
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:14px;
  color:var(--lacquer);
  text-decoration:none;
}
.wiki-link:hover{
  text-decoration:underline;
}
""".strip() + "\n"


def wrap_front(inner: str) -> str:
    return f'<div class="wrap"><div class="plate">{inner}</div></div>'


def answer_header() -> str:
    return """
{{#Wikipedia}}
<div class="wiki-panel">
  <div class="panel-title">Wikipedia</div>
  <iframe class="wiki-frame" src="{{Wikipedia}}"></iframe>
  <a class="wiki-link" href="{{Wikipedia}}">Open in browser</a>
</div>
{{/Wikipedia}}
<div class="footer">{{english_name}} | {{mandarin_name}} | {{pinyin_name}}</div>
""".strip()


def make_model() -> genanki.Model:
    templates = [
        {
            "name": "Hanzi -> Pinyin",
            "qfmt": wrap_front(
                """
<div class="eyebrow">Chinese to Pinyin</div>
<div class="hanzi">{{mandarin_name}}</div>
<div class="prompt">Read the region name in Mandarin pinyin.</div>
"""
            ),
            "afmt": wrap_front(
                """
<div class="eyebrow">Chinese to Pinyin</div>
<div class="hanzi">{{mandarin_name}}</div>
<div class="answer-panel">
  <div class="answer-label">Pinyin</div>
  <div class="answer-main">{{pinyin_name}}</div>
</div>
"""
                + answer_header()
            ),
        },
        {
            "name": "Hanzi -> English",
            "qfmt": wrap_front(
                """
<div class="eyebrow">Chinese to English</div>
<div class="hanzi">{{mandarin_name}}</div>
<div class="prompt">What is the English name of this region?</div>
"""
            ),
            "afmt": wrap_front(
                """
<div class="eyebrow">Chinese to English</div>
<div class="hanzi">{{mandarin_name}}</div>
<div class="answer-panel">
  <div class="answer-label">English</div>
  <div class="answer-main">{{english_name}}</div>
  <div class="answer-sub">{{pinyin_name}}</div>
</div>
"""
                + answer_header()
            ),
        },
        {
            "name": "English -> Chinese",
            "qfmt": wrap_front(
                """
<div class="eyebrow">English to Chinese</div>
<div class="title">{{english_name}}</div>
<div class="prompt">Recall the Chinese name in Hanzi and pinyin.</div>
"""
            ),
            "afmt": wrap_front(
                """
<div class="eyebrow">English to Chinese</div>
<div class="title">{{english_name}}</div>
<div class="answer-panel">
  <div class="answer-label">Chinese</div>
  <div class="answer-main">{{mandarin_name}}</div>
  <div class="answer-sub">{{pinyin_name}}</div>
</div>
"""
                + answer_header()
            ),
        },
        {
            "name": "Region -> Member Provinces",
            "qfmt": wrap_front(
                """
<div class="eyebrow">Region to Members</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="prompt">Which provincial-level divisions belong to this region?</div>
"""
            ),
            "afmt": wrap_front(
                """
<div class="eyebrow">Region to Members</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="connections-layout">
  <div class="map-frame">
    <div class="map-caption">Locator Map</div>
    {{Card_LocatorMap_HTML}}
  </div>
  <div class="answer-panel">
    <div class="answer-label">Members</div>
    {{Card_Member_Chips}}
  </div>
</div>
"""
                + answer_header()
            ),
        },
        {
            "name": "Members + Blank -> Locator Map",
            "qfmt": (
                "{{#Card_BlankMap_HTML}}{{#Card_LocatorMap_HTML}}"
                + wrap_front(
                    """
<div class="eyebrow">Members to Map</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="member-map-layout">
  <div class="answer-panel">
    <div class="answer-label">Members</div>
    {{Card_Member_Chips}}
  </div>
  <div class="map-frame">
    <div class="map-caption">Blank Map</div>
    {{Card_BlankMap_HTML}}
  </div>
</div>
<div class="prompt">Use the member set to place the region on the blank map, then reveal the locator.</div>
"""
                )
                + "{{/Card_LocatorMap_HTML}}{{/Card_BlankMap_HTML}}"
            ),
            "afmt": (
                "{{#Card_BlankMap_HTML}}{{#Card_LocatorMap_HTML}}"
                + wrap_front(
                    """
<div class="eyebrow">Members to Map</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="map-stack">
  <div class="map-frame">
    <div class="map-caption">Blank Map</div>
    {{Card_BlankMap_HTML}}
  </div>
  <div class="map-frame">
    <div class="map-caption">Locator Map</div>
    {{Card_LocatorMap_HTML}}
  </div>
</div>
<div class="answer-panel">
  <div class="answer-label">Members</div>
  {{Card_Member_Chips}}
</div>
"""
                    + answer_header()
                )
                + "{{/Card_LocatorMap_HTML}}{{/Card_BlankMap_HTML}}"
            ),
        },
        {
            "name": "Region -> Connections",
            "qfmt": wrap_front(
                """
<div class="eyebrow">Region to Connections</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="prompt">Recall the bordering provinces, seas, and neighboring countries.</div>
"""
            ),
            "afmt": wrap_front(
                """
<div class="eyebrow">Region to Connections</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="connections-layout">
  <div class="map-frame">
    <div class="map-caption">Locator Map</div>
    {{Card_LocatorMap_HTML}}
  </div>
  <div class="panel">
    <div class="panel-title">Connections</div>
    {{Card_Connections_HTML}}
  </div>
</div>
"""
                + answer_header()
            ),
        },
        {
            "name": "Region + Blank -> Locator Map",
            "qfmt": (
                "{{#Card_BlankMap_HTML}}{{#Card_LocatorMap_HTML}}"
                + wrap_front(
                    """
<div class="eyebrow">Atlas Recall</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="prompt">Picture the region on a blank map of China, then reveal the locator map.</div>
<div class="map-stack">
  <div class="map-frame">
    <div class="map-caption">Blank Map</div>
    {{Card_BlankMap_HTML}}
  </div>
</div>
"""
                )
                + "{{/Card_LocatorMap_HTML}}{{/Card_BlankMap_HTML}}"
            ),
            "afmt": (
                "{{#Card_BlankMap_HTML}}{{#Card_LocatorMap_HTML}}"
                + wrap_front(
                    """
<div class="eyebrow">Atlas Recall</div>
<div class="title">{{english_name}}</div>
<div class="subtitle">{{mandarin_name}} | {{pinyin_name}}</div>
<div class="map-stack">
  <div class="map-frame">
    <div class="map-caption">Blank Map</div>
    {{Card_BlankMap_HTML}}
  </div>
  <div class="map-frame">
    <div class="map-caption">Locator Map</div>
    {{Card_LocatorMap_HTML}}
  </div>
</div>
"""
                    + answer_header()
                )
                + "{{/Card_LocatorMap_HTML}}{{/Card_BlankMap_HTML}}"
            ),
        },
        {
            "name": "Locator Map -> Region Name",
            "qfmt": (
                "{{#Card_LocatorMap_HTML}}"
                + wrap_front(
                    """
<div class="eyebrow">Map to Name</div>
<div class="map-frame">
  <div class="map-caption">Locator Map</div>
  {{Card_LocatorMap_HTML}}
</div>
<div class="prompt">Name the highlighted region in English, Hanzi, and pinyin.</div>
"""
                )
                + "{{/Card_LocatorMap_HTML}}"
            ),
            "afmt": (
                "{{#Card_LocatorMap_HTML}}"
                + wrap_front(
                    """
<div class="eyebrow">Map to Name</div>
<div class="map-frame">
  <div class="map-caption">Locator Map</div>
  {{Card_LocatorMap_HTML}}
</div>
<div class="answer-panel">
  <div class="answer-label">Region</div>
  <div class="answer-main">{{english_name}}</div>
  <div class="answer-sub">{{mandarin_name}} | {{pinyin_name}}</div>
</div>
"""
                    + answer_header()
                )
                + "{{/Card_LocatorMap_HTML}}"
            ),
        },
    ]

    for template in templates:
        template["afmt"] = str(template["afmt"]).rstrip("\n") + "\n"

    return genanki.Model(
        model_id=MODEL_ID,
        name=f"China Regions v{MODEL_SCHEMA_VERSION}",
        fields=[{"name": field} for field in fieldnames_for_model()],
        templates=templates,
        css=model_css(),
    )


def note_fields(row: dict[str, str]) -> list[str]:
    member_provinces = row.get("member_provinces", "")
    connections = row.get("connections", "")
    members = split_csv_like_values(member_provinces)
    member_chips = html_member_chips(members)
    connection_html = html_connection_rows(split_connection_lines(connections))

    blank_map_path = MEDIA_DIR / BLANK_MAP_FILENAME
    blank_map_html = ""
    if blank_map_path.exists():
        blank_map_html = make_map_html(BLANK_MAP_FILENAME, "Blank map of China", "blank-map")

    locator_map_html = ""
    locator_url = (row.get("locator_map") or "").strip()
    locator_filename = LOCATOR_URL_TO_FILENAME.get(locator_url)
    if locator_filename and (MEDIA_DIR / locator_filename).exists():
        locator_map_html = make_map_html(
            locator_filename,
            f"Locator map for {row.get('english_name', '').strip()}",
            "locator-map",
        )

    return [
        row.get("mandarin_name", ""),
        row.get("blank_map", ""),
        row.get("locator_map", ""),
        row.get("pinyin_name", ""),
        row.get("english_name", ""),
        member_provinces,
        connections,
        member_chips,
        connection_html,
        blank_map_html,
        locator_map_html,
        row.get("Wikipedia", ""),
    ]


def build_deck() -> None:
    rows = read_rows(NOTES_CSV)
    model = make_model()
    deck = genanki.Deck(DECK_ID, "China Regions")
    for row in rows:
        note = genanki.Note(model=model, fields=note_fields(row))
        deck.add_note(note)

    package = genanki.Package(deck)
    package.media_files = ensure_required_media(rows)
    OUTPUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    package.write_to_file(str(OUTPUT_APKG))
    print(f"wrote {OUTPUT_APKG}")


if __name__ == "__main__":
    build_deck()
