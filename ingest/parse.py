from bs4 import BeautifulSoup
import re
from pathlib import Path


def parse_book(html_path: str) -> list[dict]:
    soup = BeautifulSoup(Path(html_path).read_text("utf-8"), "lxml")
    records = []

    for sect1 in soup.select("div.sect1"):
        chapter_tag = sect1.find(["h2"])
        chapter_title = (chapter_tag.get_text(strip=True)
                         if chapter_tag else "Unknown")
        chapter_id = chapter_tag.get("id", "") if chapter_tag else ""

        for sect2 in sect1.select("div.sect2"):
            section_tag = sect2.find(["h3", "h4"])
            section_title = (section_tag.get_text(strip=True)
                             if section_tag else "Unknown")
            section_id = section_tag.get("id", "") if section_tag else ""

            # Extract code blocks separately — preserve them intact
            code_blocks = []
            for listing in sect2.select("div.listingblock"):
                code = listing.get_text(separator="\n", strip=True)
                code_blocks.append(code)
                listing.decompose()  # remove from tree before prose extraction

            # Now get clean prose
            prose = sect2.get_text(separator=" ", strip=True)
            prose = re.sub(r"\s+", " ", prose).strip()

            records.append({
                "chapter_id":     chapter_id,
                "chapter_title":  chapter_title,
                "section_id":     section_id,
                "section_title":  section_title,
                "prose":          prose,
                "code_blocks":    code_blocks,  # list of strings
                "commands":       extract_commands(code_blocks),
            })

    return records


def extract_commands(code_blocks: list[str]) -> list[str]:
    """Pull out lines that look like shell commands."""
    commands = []
    for block in code_blocks:
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("$"):
                commands.append(line.lstrip("$ "))
            elif line.startswith("git "):
                commands.append(line)
    return list(dict.fromkeys(commands))  # dedupe, preserve order
