import json
import re
import sys
import time
from pathlib import Path

import requests

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Evidencias" / "web"
CHALLENGE_URL = "https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/"
HOME_URL = "https://www.spaceappschallenge.org/2026/"
FAQ_URL = "https://www.spaceappschallenge.org/resources/participant-faqs/"
GRAPHQL = "https://api.spaceappschallenge.org/graphql"
TITLE = "Interplanetary Survival Guide: Martian Map"


def fetch(url, name):
    response = requests.get(url, timeout=60, headers={"User-Agent": "AresAtlas/0.1"})
    response.raise_for_status()
    path = OUT / name
    path.write_bytes(response.content)
    print(f"[{response.status_code}] {len(response.content):>8} B  {path.name}")
    return response.text


def fetch_challenge_metadata():
    query = """
    query {
      challenges(first: 100) {
        totalCount
        edges {
          node {
            id
            title
            excerpt
          }
        }
      }
    }
    """
    response = requests.post(GRAPHQL, json={"query": query}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    matches = [
        edge["node"]
        for edge in payload.get("data", {}).get("challenges", {}).get("edges", [])
        if edge.get("node", {}).get("title") == TITLE
    ]
    return payload, matches


def extract_flight_fields(html):
    text = html.replace('\\"', '"').replace("\\u0026", "&")
    fields = {}
    slug = re.search(r'"slug":"([^"]+)"', text)
    if slug:
        fields["slug"] = slug.group(1)
    categories = re.search(r'"categories":(\[[^\]]*\])', text)
    if categories:
        try:
            fields["categories"] = json.loads(categories.group(1))
        except Exception:
            fields["categories_raw"] = categories.group(1)
    skills = re.search(r'"skills":(\[[^\]]*\])', text)
    if skills:
        try:
            fields["skills"] = json.loads(skills.group(1))
        except Exception:
            fields["skills_raw"] = skills.group(1)
    excerpt = re.search(r'"excerpt":"((?:[^"\\]|\\.)*)"', text)
    if excerpt:
        fields["excerpt"] = excerpt.group(1).replace('\\n', ' ').strip()
    return fields


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    challenge_html = fetch(CHALLENGE_URL, "spaceapps_2026_challenge.html")
    fetch(HOME_URL, "spaceapps_2026_home.html")
    fetch(FAQ_URL, "spaceapps_2026_faq.html")

    payload, matches = fetch_challenge_metadata()
    metadata = {
        "consultado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "titulo_buscado": TITLE,
        "coincidencias": matches,
        "flight": extract_flight_fields(challenge_html),
    }
    (OUT / "spaceapps_2026_challenge.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
