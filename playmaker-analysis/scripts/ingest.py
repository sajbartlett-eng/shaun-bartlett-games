"""
Task 1: extract all 75 player cards from the rating-system PDF into a CSV.

Reads the PDF read-only. Card pages are laid out in 4 text columns, so each
column is cropped and read top to bottom, then the stream is parsed.

Output:
  data/cards.csv           one row per card, offence + defence, tier per stat
  data/ingest_log.csv      anything ambiguous or missing
Usage:
  PLAYMAKER_PDF=/path/to/pdf python3 ingest.py
"""
import csv
import re
import sys

import pdfplumber

import config as C

# PDF field label -> CSV key. Shooting labels repeat in the offence and
# defence sections, so section context decides the prefix.
SKILL_LABELS = {
    "Height": "height", "Strength": "strength", "Speed": "speed", "Vertical": "vertical",
    "Handles": "handles", "Pressure Defence": "pressure_def", "Pass": "pass",
    "Intercept": "intercept", "Screen": "screen", "Screen Defence": "screen_def",
    "Foul (stl)": "foul_stl", "Steal": "steal", "Foul (Blk)": "foul_blk", "Block": "block",
}
SHOT_LABELS = {"Layup": "layup", "Dunk": "dunk", "Post Move": "post", "Floater": "floater",
               "Mid-range": "mid", "Long-2pts": "long2", "3-Pointer": "three", "Free Throw": "ft"}
EXPECTED_FIELDS = (list(SKILL_LABELS.values())
                   + ["off_" + v for v in SHOT_LABELS.values()]
                   + ["def_" + v for v in SHOT_LABELS.values() if v != "ft"])
TYPE_NAMES = {  # [PDF] p58 "Player Type Clarifications"
    "PG-1": "Pass First", "PG-2": "Scorer", "PG-3": "Defender", "PG-4": "Combo", "PG-5": "Slasher",
    "SG-1": "Sharpshooter", "SG-2": "Two-Way", "SG-3": "3 and D", "SG-4": "Playmaker", "SG-5": "Bucket Getter",
    "SF-1": "Scorer", "SF-2": "Two-Way", "SF-3": "Stretch", "SF-4": "Point Forward", "SF-5": "Defender",
    "PF-1": "Post Scorer", "PF-2": "Stretch", "PF-3": "Defender", "PF-4": "All-Rounder", "PF-5": "Pick and Pop",
    "C-1": "Post Scorer", "C-2": "Rim Protector", "C-3": "Stretch", "C-4": "Playmaker", "C-5": "Rim Runner",
}


def column_stream(pdf_path):
    """Return the card pages as one list of text lines, column by column."""
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for pn in C.CARD_PAGES:
            page = pdf.pages[pn - 1]
            for (x0, x1) in C.COLUMN_BOUNDS:
                text = page.crop((x0, 0, x1, page.height)).extract_text() or ""
                lines.extend((pn, ln.strip()) for ln in text.splitlines() if ln.strip())
    return lines


def tier_of(key, value, position=None):
    """Colour band for a value, using the PDF's bands. Returns (colour, note)."""
    spec = C.STATS[key]
    hits = []
    for colour, (lo, hi) in spec["bands"].items():
        if (lo is None or value >= lo) and (hi is None or value <= hi):
            hits.append(colour)
    if len(hits) == 1:
        return hits[0], ""
    if len(hits) > 1:
        return "/".join(hits), "value sits in two overlapping PDF bands"
    # Outside every band: say which side
    best = "green"
    worst = "red"
    g_lo, g_hi = spec["bands"]["green"]
    if spec["better"] == "high":
        if g_hi is not None and value > g_hi:
            return best, "above the top of the green band"
    else:
        if g_lo is not None and value < g_lo:
            return best, "below the bottom of the green band (better than green)"
    r_lo, r_hi = spec["bands"]["red"]
    if spec["better"] == "high" and r_lo is not None and value < r_lo:
        return worst, "below the bottom of the red band"
    if spec["better"] == "low" and r_hi is not None and value > r_hi:
        return worst, "above the top of the red band"
    return "gap", "falls in a gap between PDF bands"


def parse(lines):
    cards, log = [], []
    type_code, type_name_parts, card, section = None, [], None, None
    pending_label = None
    for pn, ln in lines:
        m = re.match(r"^(PG|SG|SF|PF|C)-(\d)\b(.*)$", ln)
        if m:
            type_code = f"{m.group(1)}-{m.group(2)}"
            type_name_parts = [m.group(3).strip()]
            continue
        m = re.match(r"^Tier ([ABC])$", ln)
        if m:
            card = {"type_code": type_code, "position": type_code.split("-")[0],
                    "type_name": TYPE_NAMES[type_code], "card_tier": m.group(1),
                    "card_colour": C.TIER_TO_COLOUR[m.group(1)], "source_page": pn}
            card["card_id"] = f"{type_code}{m.group(1)}"
            pdf_name = " ".join(p for p in type_name_parts if p).strip()
            if pdf_name and not TYPE_NAMES[type_code].startswith(pdf_name.split()[0]):
                log.append((card["card_id"], "type_name", f"PDF heading '{pdf_name}' vs p58 '{TYPE_NAMES[type_code]}'"))
            cards.append(card)
            section = "athletic"
            continue
        if card is None:
            continue
        if ln.startswith("Athletic Profile"):
            section = "athletic"; continue
        if ln.startswith("Skills Profile"):
            section = "skills"; continue
        if ln.startswith("Offensive Shooting Profile"):
            section = "off"; continue
        if ln.startswith("Defensive Shot Impact"):
            section = "def"; continue
        if ln.startswith("Wildcard Trait"):
            card["wildcard"] = ln.split(":", 1)[1].strip(); continue
        # continuation of a heading such as "PG-1 Pass" / "First"
        if not ln.startswith("•") and pending_label is None and not re.match(r"^\d", ln):
            if card is cards[-1] and section == "athletic" and "height" not in card:
                type_name_parts.append(ln)
            continue
        if pending_label is not None and re.match(r"^\d+(\.\d+)?$", ln):
            store(card, section, pending_label, ln, log)
            pending_label = None
            continue
        m = re.match(r"^•\s*(.+?):\s*(\d+(?:\.\d+)?)?\s*$", ln)
        if m:
            label, val = m.group(1).strip(), m.group(2)
            if val is None:
                pending_label = label
            else:
                store(card, section, label, val, log)
            continue
        if ln.strip() in {"•"}:
            continue
        log.append((card.get("card_id"), "unparsed_line", ln))
    return cards, log


def store(card, section, label, val, log):
    v = float(val)
    v = int(v) if v.is_integer() else v
    if section in ("athletic", "skills"):
        key = SKILL_LABELS.get(label)
    elif section == "off":
        key = "off_" + SHOT_LABELS[label] if label in SHOT_LABELS else None
    elif section == "def":
        key = "def_" + SHOT_LABELS[label] if label in SHOT_LABELS else None
    else:
        key = None
    if key is None:
        log.append((card["card_id"], "unknown_label", f"{section}:{label}={val}"))
        return
    if key in card:
        log.append((card["card_id"], "duplicate_field", f"{key} {card[key]} then {v}"))
    card[key] = v


def main(pdf_path=C.PDF_PATH):
    lines = column_stream(pdf_path)
    cards, log = parse(lines)
    if len(cards) != 75:
        log.append(("ALL", "card_count", f"expected 75 cards, parsed {len(cards)}"))
    for card in cards:
        for f in EXPECTED_FIELDS:
            if f not in card:
                log.append((card["card_id"], "missing_field", f))
        if card.get("wildcard") not in (None, "?"):
            log.append((card["card_id"], "wildcard", card["wildcard"]))
        # tier per stat
        for key in C.STATS:
            if key in card:
                colour, note = tier_of(key, card[key], card["position"])
                card[key + "_tier"] = colour
                if note:
                    log.append((card["card_id"], "band_note", f"{key}={card[key]}: {note}"))
        # QS is not in the PDF; derive it so the prototype comparison and sim can use it
        card["qs_derived"] = C.QS_FROM_SPEED.get(card.get("speed"), 0)
    # Global facts worth logging once
    log.append(("ALL", "missing_stat", "PDF cards have no Quick Step (QS) rating; prototype cards do. "
                "qs_derived column maps Speed 11-12->2, 9-10->1, <=8->0 (assumption)."))
    log.append(("ALL", "wildcard", "Every card's Wildcard Trait is '?' except the example card (Transition Terror +1)."))
    log.append(("ALL", "card_tier_mapping", "Card Tier A/B/C mapped to green/orange/red (assumed from the brief)."))

    cols = (["card_id", "position", "type_code", "type_name", "card_tier", "card_colour"]
            + [k for k in C.STATS] + ["qs_derived"]
            + [k + "_tier" for k in C.STATS] + ["wildcard", "source_page"])
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(C.DATA_DIR / "cards.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for card in cards:
            w.writerow(card)
    with open(C.DATA_DIR / "ingest_log.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["card_id", "issue", "detail"])
        w.writerows(log)
    print(f"parsed {len(cards)} cards; {len(log)} log entries -> {C.DATA_DIR}")
    return cards, log


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else C.PDF_PATH)
