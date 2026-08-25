#!/usr/bin/env python3
"""Parse a community submission and add it to README.md.

Usage:
    # Interactive - prompts for fields:
    python add_community.py

    # From arguments:
    python add_community.py \
        --name "GhanaNLP" \
        --github "https://github.com/GhanaNLP" \
        --region "West Africa" \
        --country "Ghana" \
        --languages "Twi,Ewe,Ga" \
        --description "Open-source NLP for Ghanaian languages." \
        --activity "Very active"

    # From a JSON file (e.g. parsed from GitHub issue):
    python add_community.py --json submission.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

README = Path(__file__).parent / "README.md"

REGION_SECTIONS = {
    "Pan-African": "## Pan-African",
    "West Africa": "## West Africa",
    "East Africa": "## East Africa",
    "North Africa": "## North Africa",
    "Southern Africa": "## Southern Africa",
    "Central Africa": "## Central Africa",
}

COUNTRY_HEADER_TEMPLATE = "### {country}"


def find_or_create_country_section(readme: str, region: str, country: str) -> str:
    """Find the country subsection within a region, or create it."""
    region_marker = REGION_SECTIONS[region]
    country_header = COUNTRY_HEADER_TEMPLATE.format(country=country)

    # Check if country section already exists in this region
    if country_header in readme:
        return readme

    # Find the region section and insert a new country subsection
    # We insert before the next ## section (next region) or end of file
    region_idx = readme.find(region_marker)
    if region_idx == -1:
        print(f"Error: Region section '{region}' not found in README.md")
        sys.exit(1)

    # Find the next ## header after this region
    next_region = re.search(r"\n## ", readme[region_idx + len(region_marker) :])
    if next_region:
        insert_idx = region_idx + len(region_marker) + next_region.start()
    else:
        insert_idx = len(readme)

    # Build the new country section
    # Check if there's already a table in this region (to know if we need a header)
    region_content = readme[region_idx:insert_idx]
    has_table = "| Community" in region_content or "| :" in region_content

    if not has_table:
        # First entry in this region - add table header
        new_section = f"""
{country_header}

| Community | GitHub | Description |
| :-- | :-- | :-- |
"""
    else:
        new_section = f"""
{country_header}

| Community | GitHub | Description |
| :-- | :-- | :-- |
"""

    readme = readme[:insert_idx] + new_section + readme[insert_idx:]
    return readme


def build_row(name: str, github: str, description: str) -> str:
    """Build a markdown table row."""
    if github:
        github_cell = f"[{github.split('/')[-1]}]({github})"
    else:
        github_cell = "-"
    return f"| {name} | {github_cell} | {description} |"


def add_community(
    name: str,
    region: str,
    country: str,
    description: str,
    github: str = "",
    website: str = "",
    languages: str = "",
    activity: str = "",
) -> None:
    """Add a community entry to the README."""
    readme = README.read_text(encoding="utf-8")

    # Validate region
    if region not in REGION_SECTIONS:
        print(f"Error: Unknown region '{region}'. Must be one of: {list(REGION_SECTIONS.keys())}")
        sys.exit(1)

    # Ensure country section exists
    readme = find_or_create_country_section(readme, region, country)

    # Find the table in the country section and append the row
    country_header = COUNTRY_HEADER_TEMPLATE.format(country=country)
    country_idx = readme.find(country_header)

    # Find the table header row (| Community | ...)
    table_header_pattern = r"\| Community \| .* \| Description \|"
    table_match = re.search(table_header_pattern, readme[country_idx:])
    if not table_match:
        print(f"Error: Could not find table header in {country} section")
        sys.exit(1)

    # Find the separator row (| :-- | ...)
    separator_pattern = r"\| :-- \|"
    sep_match = re.search(separator_pattern, readme[country_idx + table_match.end() :])
    if not sep_match:
        print("Error: Could not find table separator row")
        sys.exit(1)

    # Insert position is right after the separator row
    insert_idx = country_idx + table_match.end() + sep_match.end()

    # Find end of separator line
    newline_after_sep = readme.find("\n", insert_idx)
    if newline_after_sep != -1:
        insert_idx = newline_after_sep

    row = build_row(name, github, description)
    readme = readme[:insert_idx] + "\n" + row + readme[insert_idx:]

    README.write_text(readme, encoding="utf-8")
    print(f"Added '{name}' under {country} ({region})")


def interactive_mode() -> dict:
    """Prompt for all fields interactively."""
    print("=== Add a Community ===\n")
    fields = {
        "name": "Community / Organization Name",
        "github": "GitHub URL (or leave blank)",
        "website": "Website (or leave blank)",
        "region": f"Region ({', '.join(REGION_SECTIONS.keys())})",
        "country": "Country",
        "languages": "Languages (comma-separated, or leave blank)",
        "description": "Description (1-2 sentences)",
        "activity": "Activity level (Very active / Active / New / Inactive)",
    }
    values = {}
    for key, prompt in fields.items():
        values[key] = input(f"{prompt}: ").strip()
    return values


def main():
    parser = argparse.ArgumentParser(description="Add a community to README.md")
    parser.add_argument("--name", help="Community name")
    parser.add_argument("--github", help="GitHub URL", default="")
    parser.add_argument("--website", help="Website URL", default="")
    parser.add_argument("--region", help="Region")
    parser.add_argument("--country", help="Country")
    parser.add_argument("--languages", help="Languages (comma-separated)", default="")
    parser.add_argument("--description", help="Description")
    parser.add_argument("--activity", help="Activity level", default="")
    parser.add_argument("--json", help="Path to JSON file with submission data")

    args = parser.parse_args()

    if args.json:
        data = json.loads(Path(args.json).read_text())
    elif args.name and args.region and args.country and args.description:
        data = vars(args)
        del data["json"]
    else:
        data = interactive_mode()

    add_community(
        name=data.get("name", ""),
        github=data.get("github", ""),
        website=data.get("website", ""),
        region=data.get("region", ""),
        country=data.get("country", ""),
        languages=data.get("languages", ""),
        description=data.get("description", ""),
        activity=data.get("activity", ""),
    )


if __name__ == "__main__":
    main()
