"""
SmartHandyman — единый парсер всех источников
==============================================
Источники: iFixit, WikiHow, BobVila, Mastergrad

Запуск:
    pip install requests beautifulsoup4 tqdm
    python scraper.py                        # все источники
    python scraper.py --sources ifixit wikihow  # только выбранные
    python scraper.py --clean-only           # только чистка уже скачанных файлов

Файлы прогресса сохраняются автоматически — можно прерывать и продолжать.
"""

import argparse
import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm

# ══════════════════════════════════════════════════════════════════════════════
# НАСТРОЙКИ
# ══════════════════════════════════════════════════════════════════════════════

OUTPUT_DIR = Path(".")   # куда сохранять jsonl файлы

IFIXIT = dict(
    output="smarthandyman_ifixit.jsonl",
    progress="progress_ifixit.json",
    delay=0.4,
    max_retries=3,
)

WIKIHOW = dict(
    output="smarthandyman_wikihow.jsonl",
    progress="progress_wikihow.json",
    delay=1.2,
    max_retries=3,
)

BOBVILA = dict(
    output="smarthandyman_bobvila.jsonl",
    progress="progress_bobvila.json",
    delay=1.5,
    max_retries=3,
    max_pages=20,
)

MASTERGRAD = dict(
    output="smarthandyman_mastergrad.jsonl",
    progress="progress_mastergrad.json",
    delay=1.5,
    max_retries=3,
    max_pages=30,
    max_thread_pages=10,
    min_post_len=50,
    top_threads=100,
)

# ══════════════════════════════════════════════════════════════════════════════
# КАТЕГОРИИ
# ══════════════════════════════════════════════════════════════════════════════

IFIXIT_CATEGORIES = [
    ("Plumbing",                "plumbing"),
    ("Toilet",                  "plumbing"),
    ("Faucet",                  "plumbing"),
    ("Water Heater",            "plumbing"),
    ("Shower Head",             "plumbing"),
    ("Water Filtration System", "plumbing"),
    ("Electrical",              "electrical"),
    ("Electrical USA",          "electrical"),
    ("Electrical EU",           "electrical"),
    ("Door And Window",         "doors_windows"),
    ("Door Handle",             "doors_windows"),
    ("Garage Door Opener",      "doors_windows"),
    ("Blind",                   "doors_windows"),
    ("Air Conditioning",        "hvac"),
    ("Boiler",                  "hvac"),
    ("Heat Pump",               "hvac"),
    ("Furnace",                 "hvac"),
    ("Space Heater",            "hvac"),
    ("Fan",                     "hvac"),
    ("Refrigerator",            "appliance"),
    ("Washing Machine",         "appliance"),
    ("Dryer",                   "appliance"),
    ("Dishwasher",              "appliance"),
    ("Stove",                   "appliance"),
    ("Freezer",                 "appliance"),
    ("Vacuum Cleaner",          "appliance"),
    ("Microwave",               "appliance"),
    ("Garbage Disposal",        "appliance"),
]

WIKIHOW_CATEGORIES = [
    ("Air-Conditioning",                    "hvac"),
    ("Apartment-Living",                    "home_maintenance"),
    ("Basement-Water-Problems",             "plumbing"),
    ("Basements-and-Cellars",               "home_maintenance"),
    ("Bathrooms",                           "home_maintenance"),
    ("Bathtubs",                            "plumbing"),
    ("Blocked-Drains",                      "plumbing"),
    ("Brickwork-and-Stone-Masonry",         "construction"),
    ("Building-Roofs",                      "construction"),
    ("Building-Walls",                      "construction"),
    ("Building-Workbenches",                "diy"),
    ("Cabinets-and-Cupboards",              "home_maintenance"),
    ("Carpets-and-Rugs",                    "flooring"),
    ("Caulking",                            "home_maintenance"),
    ("Ceiling-Fans",                        "electrical"),
    ("Ceilings",                            "home_maintenance"),
    ("Cleaning",                            "home_maintenance"),
    ("Cleaning-Floors",                     "flooring"),
    ("Concrete",                            "construction"),
    ("Cooking-Appliances",                  "appliance"),
    ("Countertops-and-Kitchen-Benches",     "home_maintenance"),
    ("DIY",                                 "diy"),
    ("Disaster-Preparedness",               "home_maintenance"),
    ("Dishwasher-Repairs",                  "appliance"),
    ("Dishwashers",                         "appliance"),
    ("Door-Installation",                   "doors_windows"),
    ("Door-Repairs",                        "doors_windows"),
    ("Door-Security",                       "doors_windows"),
    ("Door-Types",                          "doors_windows"),
    ("Doors-and-Windows",                   "doors_windows"),
    ("Drains",                              "plumbing"),
    ("Dryer-Repairs",                       "appliance"),
    ("Electrical-Maintenance",              "electrical"),
    ("Electrical-Power-Storage",            "electrical"),
    ("Electrical-Projects",                 "electrical"),
    ("Electrical-Safety",                   "electrical"),
    ("Electrical-Wiring-and-Safety-Switches", "electrical"),
    ("Electrical-and-Electronic-Circuits",  "electrical"),
    ("Fans-and-Ventilation",                "hvac"),
    ("Fastening-Tools",                     "diy"),
    ("Faucet-Repairs",                      "plumbing"),
    ("Faucets-and-Taps",                    "plumbing"),
    ("Fences-and-Gates",                    "yard"),
    ("Fireplaces",                          "hvac"),
    ("Floor-Care-Appliances",               "appliance"),
    ("Floor-Repairs",                       "flooring"),
    ("Floor-Types",                         "flooring"),
    ("Floors-and-Stairs",                   "flooring"),
    ("Furnaces",                            "hvac"),
    ("Furniture",                           "home_maintenance"),
    ("Furniture-Fixes",                     "home_maintenance"),
    ("Garage-Doors",                        "doors_windows"),
    ("Garages",                             "home_maintenance"),
    ("Hanging-Things",                      "home_maintenance"),
    ("Heater-Appliances",                   "hvac"),
    ("Heating-Systems",                     "hvac"),
    ("Heating-and-Cooling",                 "hvac"),
    ("Hinges",                              "doors_windows"),
    ("Holding-and-Support-Tools",           "diy"),
    ("Hole-Making-Tools",                   "diy"),
    ("Home-Appliances",                     "appliance"),
    ("Home-Improvements",                   "home_maintenance"),
    ("Home-Maintenance",                    "home_maintenance"),
    ("Home-Repairs",                        "home_maintenance"),
    ("Home-Security",                       "home_maintenance"),
    ("Hot-Tubs",                            "plumbing"),
    ("House-Building",                      "construction"),
    ("Housekeeping",                        "home_maintenance"),
    ("Humidity-Appliances",                 "hvac"),
    ("Indoor-Air-Improvement",              "hvac"),
    ("Insulation",                          "hvac"),
    ("Interior-Walls",                      "home_maintenance"),
    ("Kitchen-Appliances",                  "appliance"),
    ("Kitchen-Cabinets",                    "home_maintenance"),
    ("Kitchen-Countertop-Appliances",       "appliance"),
    ("Kitchen-Remodel-and-Renovation",      "home_maintenance"),
    ("Kitchens",                            "home_maintenance"),
    ("Light-Bulbs",                         "electrical"),
    ("Light-Switches",                      "electrical"),
    ("Lighting",                            "electrical"),
    ("Locks-and-Keys",                      "doors_windows"),
    ("Measuring-Power-Current-and-Energy",  "electrical"),
    ("Measuring-and-Marking-Tools",         "diy"),
    ("Moisture-Protection-and-Prevention",  "home_maintenance"),
    ("Mold-and-Mildew-Treatment",           "home_maintenance"),
    ("Motors-Generators-and-Transformers",  "electrical"),
    ("Outdoor-Lights",                      "electrical"),
    ("Pest-Control",                        "home_maintenance"),
    ("Piping",                              "plumbing"),
    ("Plumbing",                            "plumbing"),
    ("Radiators-for-Buildings",             "hvac"),
    ("Rain-Gutters-and-Downspouts",         "roofing"),
    ("Refrigerators-and-Freezers",          "appliance"),
    ("Renovation-Advice-and-Tips",          "home_maintenance"),
    ("Roof-Maintenance",                    "roofing"),
    ("Roofs",                               "roofing"),
    ("Security-Systems",                    "home_maintenance"),
    ("Shaping-Tools",                       "diy"),
    ("Showers",                             "plumbing"),
    ("Siding",                              "construction"),
    ("Sinks",                               "plumbing"),
    ("Soundproofing",                       "home_maintenance"),
    ("Storms",                              "home_maintenance"),
    ("Swimming-Pool-Equipment",             "plumbing"),
    ("Swimming-Pool-Maintenance",           "plumbing"),
    ("Swimming-Pool-Water-Treatment",       "plumbing"),
    ("Swimming-Pools",                      "plumbing"),
    ("Tiles-and-Tiling",                    "flooring"),
    ("Toilet-Maintenance",                  "plumbing"),
    ("Toilet-Repairs",                      "plumbing"),
    ("Toilets",                             "plumbing"),
    ("Tools",                               "diy"),
    ("Vacuum-Cleaners",                     "appliance"),
    ("Wall-Repairs",                        "home_maintenance"),
    ("Walls-and-Ceilings",                  "home_maintenance"),
    ("Washing-Machine-Repairs",             "appliance"),
    ("Washing-Machines-and-Dryers",         "appliance"),
    ("Waste-Removal-Systems",               "plumbing"),
    ("Water",                               "plumbing"),
    ("Water-Filters",                       "plumbing"),
    ("Water-Heating-Systems",               "plumbing"),
    ("Winterization",                       "hvac"),
    ("Woodworking-Tools",                   "diy"),
    ("Working-with-Concrete-and-Cement",    "construction"),
    ("Yard-and-Outdoors",                   "yard"),
]

BOBVILA_CATEGORIES = [
    ("plumbing",       "plumbing"),
    ("hvac",           "hvac"),
    ("appliances",     "appliance"),
    ("flooring",       "flooring"),
    ("roofing",        "roofing"),
    ("windows",        "doors_windows"),
    ("doors",          "doors_windows"),
    ("walls-ceilings", "home_maintenance"),
    ("diy",            "diy"),
]

MASTERGRAD_FORUMS = [
    ("otoplenie-vodosnabzhenie-kanalizaciya-i-santehnicheskoe-oborudovanie/santehnika-i-santehnicheskoe-oborudovanie", "plumbing"),
    ("otoplenie-vodosnabzhenie-kanalizaciya-i-santehnicheskoe-oborudovanie/vodosnabzhenie",                            "plumbing"),
    ("otoplenie-vodosnabzhenie-kanalizaciya-i-santehnicheskoe-oborudovanie/kanalizaciya",                              "plumbing"),
    ("otoplenie-vodosnabzhenie-kanalizaciya-i-santehnicheskoe-oborudovanie/otoplenie",                                 "hvac"),
    ("otoplenie-vodosnabzhenie-kanalizaciya-i-santehnicheskoe-oborudovanie/kotly-i-kotelnoe-oborudovanie",             "hvac"),
    ("elektrika-i-slabotochka/elektrika",                                                                              "electrical"),
    ("ventilyaciya-i-kondicionirovanie",                                                                               "hvac"),
    ("okna-dveri-osteklenie-domov-i-kvartir",                                                                          "doors_windows"),
    ("remont-kvartir-pereplanirovka-otdelka/steny-i-pereplanirovki",                                                   "home_maintenance"),
    ("remont-kvartir-pereplanirovka-otdelka/teplyy-pol",                                                               "flooring"),
    ("individualnye-doma-i-postroyki/pol-i-napolnye-pokrytiya",                                                        "flooring"),
    ("individualnye-doma-i-postroyki/potolki",                                                                         "home_maintenance"),
    ("individualnye-doma-i-postroyki/krovlya",                                                                         "roofing"),
    ("bytovaya-tehnika-i-elektronika/holodilniki",                                                                     "appliance"),
    ("bytovaya-tehnika-i-elektronika/stiralnye-mashiny",                                                               "appliance"),
    ("bytovaya-tehnika-i-elektronika/posudomoechnye-mashiny",                                                          "appliance"),
    ("bytovaya-tehnika-i-elektronika/pylesosy",                                                                        "appliance"),
    ("stroitelnye-i-otdelochnye-materialy/plitka",                                                                     "home_maintenance"),
]

# ══════════════════════════════════════════════════════════════════════════════
# ОБЩИЕ УТИЛИТЫ
# ══════════════════════════════════════════════════════════════════════════════

def load_progress(path: str) -> dict:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return {}

def save_progress(path: str, data: dict):
    Path(path).write_text(json.dumps(data, indent=2))

def fetch_html(url: str, headers: dict, max_retries: int, timeout: int = 15) -> BeautifulSoup | None:
    for attempt in range(max_retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"\n  ⚠ {url}: {e}")
                return None

def print_stats(output_file: str):
    total = 0
    domains: dict[str, int] = {}
    for line in open(output_file, encoding="utf-8"):
        d = json.loads(line).get("domain", "?")
        domains[d] = domains.get(d, 0) + 1
        total += 1
    print(f"\n✅ {total} документов → {output_file}")
    print("📊 По доменам:")
    for d, cnt in sorted(domains.items(), key=lambda x: -x[1]):
        print(f"   {d}: {cnt}")

# ══════════════════════════════════════════════════════════════════════════════
# IFIXIT
# ══════════════════════════════════════════════════════════════════════════════

def run_ifixit():
    cfg = IFIXIT
    base_url = "https://www.ifixit.com/api/2.0"
    output = str(OUTPUT_DIR / cfg["output"])
    progress = load_progress(cfg["progress"])
    done_categories = set(progress.get("done_categories", []))
    done_ids = set(progress.get("done_guide_ids", []))

    def api_get(url, params=None):
        for attempt in range(cfg["max_retries"]):
            try:
                r = requests.get(url, params=params, timeout=15)
                r.raise_for_status()
                return r.json()
            except requests.exceptions.RequestException as e:
                if attempt < cfg["max_retries"] - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"\n  ⚠ {url}: {e}")
                    return None

    def get_guide_ids(category):
        ids = []
        offset, limit = 0, 50
        while True:
            data = api_get(
                f"{base_url}/wikis/CATEGORY/{requests.utils.quote(category)}",
                params={"limit": limit, "offset": offset},
            )
            if not data:
                break
            guides = data.get("guides", [])
            if not guides:
                break
            ids.extend(g["guideid"] for g in guides if "guideid" in g)
            if len(guides) < limit:
                break
            offset += limit
            time.sleep(cfg["delay"])
        return ids

    def extract_guide(raw, domain):
        steps = raw.get("steps", [])
        tools = [t.get("text", "") for t in raw.get("tools", [])]
        parts = [p.get("text", "") for p in raw.get("parts", [])]
        step_docs = []
        for i, step in enumerate(steps, 1):
            text = " ".join(
                line.get("text_raw", "") for line in step.get("lines", []) if line.get("text_raw")
            ).strip()
            if text:
                step_docs.append(f"Step {i}: {text}")
        full_parts = []
        intro = (raw.get("introduction_raw") or "").strip()
        if intro:
            full_parts.append(intro)
        full_parts.extend(step_docs)
        conclusion = (raw.get("conclusion_raw") or "").strip()
        if conclusion:
            full_parts.append(conclusion)
        return {
            "source": "ifixit",
            "id": raw.get("guideid"),
            "domain": domain,
            "category": raw.get("category", ""),
            "subject": raw.get("subject", ""),
            "title": raw.get("title", ""),
            "difficulty": raw.get("difficulty", ""),
            "time_required": raw.get("time_required", ""),
            "url": raw.get("url", ""),
            "tools": tools,
            "parts": parts,
            "steps_count": len(steps),
            "text": "\n\n".join(full_parts),
        }

    print("\n🔧 iFixit scraper")
    out = open(output, "a", encoding="utf-8")

    for category, domain in IFIXIT_CATEGORIES:
        if category in done_categories:
            print(f"  ⏭  {category}")
            continue
        print(f"\n  📂 {category} [{domain}]")
        ids = get_guide_ids(category)
        new_ids = [i for i in ids if i not in done_ids]
        print(f"     Гайдов: {len(ids)} всего, {len(new_ids)} новых")

        for guide_id in tqdm(new_ids, desc=f"     {category}", unit="guide"):
            time.sleep(cfg["delay"])
            raw = api_get(f"{base_url}/guides/{guide_id}")
            if not raw:
                continue
            doc = extract_guide(raw, domain)
            if not doc["text"].strip():
                continue
            out.write(json.dumps(doc, ensure_ascii=False) + "\n")
            out.flush()
            done_ids.add(guide_id)
            save_progress(cfg["progress"], {"done_categories": list(done_categories), "done_guide_ids": list(done_ids)})

        done_categories.add(category)
        save_progress(cfg["progress"], {"done_categories": list(done_categories), "done_guide_ids": list(done_ids)})

    out.close()
    print_stats(output)

# ══════════════════════════════════════════════════════════════════════════════
# WIKIHOW
# ══════════════════════════════════════════════════════════════════════════════

def run_wikihow():
    cfg = WIKIHOW
    base_url = "https://www.wikihow.com"
    output = str(OUTPUT_DIR / cfg["output"])
    progress = load_progress(cfg["progress"])
    done_categories = set(progress.get("done_categories", []))
    done_urls = set(progress.get("done_urls", []))

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    wikihow_noise = [
        'Download Article', 'Co-authored by', 'Last Updated', 'Fact Checked',
        'Show more', 'Show less', 'Expert Interview', 'wikiHow staff writer', 'wikiHow Staff',
    ]

    def clean_text(text):
        parts = text.split('\n\n')
        return '\n\n'.join(p for p in parts if not any(n in p for n in wikihow_noise)).strip()

    def get_article_urls(slug):
        urls, seen = [], set()
        page_url = f"{base_url}/Category:{slug}"
        while page_url:
            soup = fetch_html(page_url, headers, cfg["max_retries"])
            if not soup:
                break
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if (href.startswith("/") and "Category:" not in href and "Special:" not in href
                        and "action=" not in href and "?" not in href and href not in seen and len(href) > 3):
                    seen.add(href)
                    urls.append(base_url + href)
            next_link = soup.find("a", string=lambda t: t and "next" in t.lower())
            if next_link and next_link.get("href"):
                href = next_link["href"]
                page_url = href if href.startswith("http") else base_url + href
                time.sleep(cfg["delay"])
            else:
                break
        return urls

    def extract_article(soup, url, domain):
        title_tag = soup.find("h1", class_="whb") or soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            return None
        intro_tag = soup.find("div", id="intro") or soup.find("p", class_="whb")
        intro = intro_tag.get_text(" ", strip=True) if intro_tag else ""
        steps = []
        for i, step_div in enumerate(soup.select("div.step"), 1):
            text = step_div.get_text(" ", strip=True)
            if text:
                steps.append(f"Step {i}: {text}")
        if not steps:
            for i, li in enumerate(soup.select("li.steps_list_item"), 1):
                text = li.get_text(" ", strip=True)
                if text:
                    steps.append(f"Step {i}: {text}")
        if len(steps) < 2:
            return None
        parts = []
        if intro:
            parts.append(intro)
        parts.extend(steps)
        tips = [tip.get_text(" ", strip=True) for tip in soup.select("div#tips li")]
        if tips:
            parts.append("Tips: " + " | ".join(tips[:5]))
        full_text = clean_text("\n\n".join(parts))
        if not full_text or len(full_text) < 100:
            return None
        cats = [a.get_text(strip=True) for a in soup.select("div#breadcrumb a, nav.breadcrumb a")
                if a.get_text(strip=True) not in ("wikiHow", "Home")]
        return {
            "source": "wikihow",
            "domain": domain,
            "category": " > ".join(cats) if cats else domain,
            "title": title,
            "url": url,
            "steps_count": len(steps),
            "text": full_text,
        }

    print("\n🔧 WikiHow scraper")
    out = open(output, "a", encoding="utf-8")

    for slug, domain in WIKIHOW_CATEGORIES:
        if slug in done_categories:
            print(f"  ⏭  {slug}")
            continue
        print(f"\n  📂 {slug} [{domain}]")
        time.sleep(cfg["delay"])
        article_urls = get_article_urls(slug)
        new_urls = [u for u in article_urls if u not in done_urls]
        print(f"     Статей: {len(article_urls)} всего, {len(new_urls)} новых")

        saved = 0
        for url in tqdm(new_urls, desc=f"     {slug}", unit="art"):
            time.sleep(cfg["delay"])
            soup = fetch_html(url, headers, cfg["max_retries"])
            if not soup:
                continue
            doc = extract_article(soup, url, domain)
            if not doc:
                continue
            out.write(json.dumps(doc, ensure_ascii=False) + "\n")
            out.flush()
            saved += 1
            done_urls.add(url)
            save_progress(cfg["progress"], {"done_categories": list(done_categories), "done_urls": list(done_urls)})

        print(f"     Сохранено: {saved}")
        done_categories.add(slug)
        save_progress(cfg["progress"], {"done_categories": list(done_categories), "done_urls": list(done_urls)})

    out.close()
    print_stats(output)

# ══════════════════════════════════════════════════════════════════════════════
# BOBVILA
# ══════════════════════════════════════════════════════════════════════════════

def run_bobvila():
    cfg = BOBVILA
    base_url = "https://www.bobvila.com"
    output = str(OUTPUT_DIR / cfg["output"])
    progress = load_progress(cfg["progress"])
    done_categories = set(progress.get("done_categories", []))
    done_urls = set(progress.get("done_urls", []))

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    noise_phrases = [
        "We may earn revenue from the products available", "participate in affiliate programs",
        "Home Advice You Can Trust", "Tips, tricks & ideas for a better home",
        "delivered to your inbox", "Email address", "Sign Up", "Thank you!",
        "Terms of Service", "Privacy Policy", "Learn More", "Photo:", "RELATED:",
        "I Made This One Smart Investment", "Bob Vila Radio:",
    ]

    diy_skip = [
        "Best ", "Tested", "Reviewed", "Expert Pick", "Permaculture", "Coconut Oil",
        "Garden", "Seeds Indoor", "Upholstery Cleaner", "Snow Blower", "Lawn Mower",
        "Welding", "Sawhorse", "Jointer", "Planer", "Fire Ant", "Ice Dam", "Wildlife", "Bird",
    ]

    def is_noise(text):
        return any(p in text for p in noise_phrases)

    def get_article_urls(slug):
        urls, seen = [], set()
        for page in range(1, cfg["max_pages"] + 1):
            url = f"{base_url}/category/{slug}/" if page == 1 else f"{base_url}/category/{slug}/page/{page}/"
            soup = fetch_html(url, headers, cfg["max_retries"])
            if not soup:
                break
            found = 0
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/articles/" in href and href not in seen:
                    seen.add(href)
                    urls.append(href)
                    found += 1
            if found == 0:
                break
            time.sleep(cfg["delay"])
        return urls

    def extract_article(soup, url, domain):
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        if not title:
            return None
        if domain == "diy" and any(p in title for p in diy_skip):
            return None
        article = soup.find("article")
        if not article:
            return None
        for tag in article.select("aside, nav, footer, script, style, svg, noscript"):
            tag.decompose()
        sections, current_header, current_paras = [], None, []
        for el in article.find_all(["h2", "h3", "p", "ul", "ol"]):
            if el.name in ("h2", "h3"):
                if current_header and current_paras:
                    sections.append(f"{current_header}\n" + " ".join(current_paras))
                elif current_paras:
                    sections.append(" ".join(current_paras))
                current_header = el.get_text(strip=True)
                current_paras = []
            elif el.name == "p":
                text = el.get_text(" ", strip=True)
                if text and not is_noise(text):
                    current_paras.append(text)
            elif el.name in ("ul", "ol"):
                items = [li.get_text(" ", strip=True) for li in el.find_all("li")]
                current_paras.extend(f"• {i}" for i in items if i and not is_noise(i))
        if current_header and current_paras:
            sections.append(f"{current_header}\n" + " ".join(current_paras))
        elif current_paras:
            sections.append(" ".join(current_paras))
        clean_sections = [s for s in sections if not is_noise(s.split("\n")[0])]
        full_text = "\n\n".join(clean_sections).strip()
        if not full_text or len(full_text) < 300:
            return None
        return {
            "source": "bobvila",
            "domain": domain,
            "category": domain,
            "title": title,
            "url": url,
            "text": full_text,
        }

    print("\n🔧 BobVila scraper")
    out = open(output, "a", encoding="utf-8")

    for slug, domain in BOBVILA_CATEGORIES:
        if slug in done_categories:
            print(f"  ⏭  {slug}")
            continue
        print(f"\n  📂 {slug} [{domain}]")
        article_urls = get_article_urls(slug)
        new_urls = [u for u in article_urls if u not in done_urls]
        print(f"     Статей: {len(article_urls)} всего, {len(new_urls)} новых")

        saved = 0
        for url in tqdm(new_urls, desc=f"     {slug}", unit="art"):
            time.sleep(cfg["delay"])
            soup = fetch_html(url, headers, cfg["max_retries"])
            if not soup:
                continue
            doc = extract_article(soup, url, domain)
            if not doc:
                continue
            out.write(json.dumps(doc, ensure_ascii=False) + "\n")
            out.flush()
            saved += 1
            done_urls.add(url)
            save_progress(cfg["progress"], {"done_categories": list(done_categories), "done_urls": list(done_urls)})

        print(f"     Сохранено: {saved}")
        done_categories.add(slug)
        save_progress(cfg["progress"], {"done_categories": list(done_categories), "done_urls": list(done_urls)})

    out.close()
    print_stats(output)

# ══════════════════════════════════════════════════════════════════════════════
# MASTERGRAD
# ══════════════════════════════════════════════════════════════════════════════

def run_mastergrad():
    cfg = MASTERGRAD
    base_url = "https://www.mastergrad.com"
    output = str(OUTPUT_DIR / cfg["output"])
    progress = load_progress(cfg["progress"])
    done_forums = set(progress.get("done_forums", []))
    done_urls = set(progress.get("done_urls", []))

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }

    def get_thread_urls(forum_slug):
        threads, seen = [], set()
        for page in range(1, cfg["max_pages"] + 1):
            url = f"{base_url}/forums/{forum_slug}/" if page == 1 else f"{base_url}/forums/{forum_slug}/?page={page}"
            soup = fetch_html(url, headers, cfg["max_retries"], timeout=30)
            if not soup:
                break
            found = 0
            for row in soup.select("div.row-with-arrow"):
                a = row.find("a", href=lambda h: h and h.startswith("/forums/t") and "#" not in h and "?" not in h)
                if not a:
                    continue
                href = a["href"]
                if href in seen:
                    continue
                seen.add(href)
                text = row.get_text(" ", strip=True)
                replies = max((int(w) for w in text.split() if w.isdigit()), default=0)
                threads.append((replies, base_url + href))
                found += 1
            if found == 0:
                break
            time.sleep(cfg["delay"])
        threads.sort(key=lambda x: x[0], reverse=True)
        return [url for _, url in threads[:cfg["top_threads"]]]

    def extract_posts(soup):
        posts = []
        container = soup.find("div", id="posts-container")
        if not container:
            return posts
        for post_div in container.select("div.my-2"):
            for el in post_div.select(".author-info, .d-flex.justify-content-between, .btn, .dropdown"):
                el.decompose()
            content = (post_div.find("div", class_="pagetext")
                       or post_div.find("div", class_="post-full")
                       or post_div)
            text = content.get_text(" ", strip=True)
            if len(text) >= cfg["min_post_len"]:
                posts.append(text)
        return posts

    def scrape_thread(url, domain):
        soup = fetch_html(url, headers, cfg["max_retries"], timeout=30)
        if not soup:
            return None
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
        if not title:
            return None
        all_posts = extract_posts(soup)
        seen_posts = set(all_posts)
        for page in range(2, cfg["max_thread_pages"] + 1):
            psoup = fetch_html(f"{url}?page={page}", headers, cfg["max_retries"], timeout=30)
            if not psoup:
                break
            new_posts = [p for p in extract_posts(psoup) if p not in seen_posts]
            if not new_posts:
                break
            seen_posts.update(new_posts)
            all_posts.extend(new_posts)
            time.sleep(cfg["delay"])
        if len(all_posts) < 2:
            return None
        full_text = f"Вопрос: {all_posts[0]}\n\n" + "\n\n".join(
            f"Ответ {i+1}: {a}" for i, a in enumerate(all_posts[1:])
        )
        return {
            "source": "mastergrad",
            "domain": domain,
            "title": title,
            "url": url,
            "posts_count": len(all_posts),
            "text": full_text,
        }

    print("\n🔧 Mastergrad scraper")
    out = open(output, "a", encoding="utf-8")

    for forum_slug, domain in MASTERGRAD_FORUMS:
        if forum_slug in done_forums:
            print(f"  ⏭  {forum_slug.split('/')[-1]}")
            continue
        print(f"\n  📂 {forum_slug.split('/')[-1]} [{domain}]")
        thread_urls = get_thread_urls(forum_slug)
        new_urls = [u for u in thread_urls if u not in done_urls]
        print(f"     Тредов: {len(thread_urls)} всего, {len(new_urls)} новых")

        saved = 0
        for url in tqdm(new_urls, desc=f"     {forum_slug.split('/')[-1]}", unit="thread"):
            time.sleep(cfg["delay"])
            doc = scrape_thread(url, domain)
            if not doc:
                continue
            out.write(json.dumps(doc, ensure_ascii=False) + "\n")
            out.flush()
            saved += 1
            done_urls.add(url)
            save_progress(cfg["progress"], {"done_forums": list(done_forums), "done_urls": list(done_urls)})

        print(f"     Сохранено: {saved}")
        done_forums.add(forum_slug)
        save_progress(cfg["progress"], {"done_forums": list(done_forums), "done_urls": list(done_urls)})

    out.close()
    print_stats(output)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

RUNNERS = {
    "ifixit":     run_ifixit,
    "wikihow":    run_wikihow,
    "bobvila":    run_bobvila,
    "mastergrad": run_mastergrad,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartHandyman scraper")
    parser.add_argument(
        "--sources", nargs="+", choices=RUNNERS.keys(),
        default=list(RUNNERS.keys()),
        help="Источники для парсинга (по умолчанию все)"
    )
    args, _ = parser.parse_known_args()  # ignore jupyter args

    print("🏠 SmartHandyman unified scraper")
    print(f"   Источники: {', '.join(args.sources)}\n")

    for source in args.sources:
        RUNNERS[source]()

    print("\n✅ Всё готово!")
