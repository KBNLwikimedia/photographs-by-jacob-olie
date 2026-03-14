"""
Extract Source URLs from Wikimedia Commons file pages.

This script reads a list of Wikimedia Commons filenames (one per line) from
``filelist.txt``, fetches the wikitext of each file page via the MediaWiki API,
and extracts the value of the ``source`` parameter from the ``{{Photograph}}``
template. The results are written to an Excel workbook with three columns:
Filename, File URL (Commons), and Source URL.

The MediaWiki API is queried in batches of 50 titles (the API maximum) with a
1-second delay between batches to avoid overloading the server. A descriptive
User-Agent header is set as required by the Wikimedia User-Agent policy
(https://meta.wikimedia.org/wiki/User-Agent_policy).

Prerequisites:
    pip install requests openpyxl

Usage:
    python extract_sources.py

Input:
    filelist.txt — plain text file with one Wikimedia Commons filename per line,
    e.g. ``File:Jacob Olie 001.jpg``

Output:
    jacob_olie_sources.xlsx — Excel workbook with columns:
      A: Filename
      B: File URL (Commons)
      C: Source URL
"""

import re
import time
import requests
import openpyxl

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "JacobOlieSourceExtractor/1.0 (https://github.com/KBNLresearch; photographs-by-jacob-olie project) Python/requests"
BATCH_SIZE = 50  # API allows up to 50 titles per query
DELAY_BETWEEN_BATCHES = 1.0  # seconds between API calls

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def read_filelist(path):
    """Read a list of Wikimedia Commons filenames from a text file.

    Args:
        path: Path to a text file containing one filename per line,
              e.g. ``File:Jacob Olie 001.jpg``.

    Returns:
        A list of non-empty, stripped filename strings.
    """
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def fetch_wikitext_batch(titles):
    """Fetch the wikitext content for a batch of file pages via the MediaWiki API.

    Uses the ``query`` action with ``revisions`` and ``info`` properties to
    retrieve both the page wikitext (from the main slot) and the full URL of
    each page. Up to 50 titles can be queried in a single request.

    Args:
        titles: A list of page titles (including the ``File:`` prefix).

    Returns:
        The parsed JSON response from the MediaWiki API. Page data is in
        ``response["query"]["pages"]`` (a list when using formatversion=2).

    Raises:
        requests.HTTPError: If the API returns a non-2xx status code.
    """
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "revisions|info",
        "rvprop": "content",
        "rvslots": "main",
        "inprop": "url",
        "format": "json",
        "formatversion": "2",
    }
    resp = session.get(API_URL, params=params)
    resp.raise_for_status()
    return resp.json()


def extract_source_from_wikitext(wikitext):
    """Extract the Source URL from a ``{{Photograph}}`` template in wikitext.

    Locates the ``{{Photograph}}`` template (case-insensitive first letter),
    then finds the ``source`` parameter within it. The parser correctly handles
    nested ``{{ }}`` templates and ``[[ ]]`` wikilinks inside the value.

    If the extracted value contains a URL (``http://`` or ``https://``), only
    the URL portion is returned (stripping any surrounding wikitext markup).

    Args:
        wikitext: The full wikitext content of a Wikimedia Commons file page.

    Returns:
        The source URL as a string, or None if the ``{{Photograph}}`` template
        or ``source`` parameter is not found.
    """
    if not wikitext:
        return None

    # Find the Photograph template block (case-insensitive first letter)
    photo_match = re.search(
        r"\{\{[Pp]hotograph\b", wikitext
    )
    if not photo_match:
        return None

    # From the start of the template, find the source parameter
    template_start = photo_match.start()
    text_from_template = wikitext[template_start:]

    source_match = re.search(
        r"\|\s*[Ss]ource\s*=\s*", text_from_template
    )
    if not source_match:
        return None

    # Extract everything after "source =" until the next top-level | or }}
    value_start = source_match.end()
    value_text = text_from_template[value_start:]

    # Parse respecting nested braces and brackets
    depth_curly = 0
    depth_square = 0
    end_pos = len(value_text)
    for i, ch in enumerate(value_text):
        if ch == '{':
            depth_curly += 1
        elif ch == '}':
            if depth_curly > 0:
                depth_curly -= 1
            else:
                end_pos = i
                break
        elif ch == '[':
            depth_square += 1
        elif ch == ']':
            if depth_square > 0:
                depth_square -= 1
        elif ch == '|' and depth_curly == 0 and depth_square == 0:
            end_pos = i
            break

    source_value = value_text[:end_pos].strip()

    # If the value contains a URL, extract just the URL
    url_match = re.search(r'https?://[^\s\]\|]+', source_value)
    if url_match:
        return url_match.group(0)

    return source_value if source_value else None


def main():
    """Main entry point: read filelist, query API, write Excel output."""
    filelist_path = "filelist.txt"
    output_path = "jacob_olie_sources.xlsx"

    titles = read_filelist(filelist_path)
    total = len(titles)
    print(f"Read {total} file titles from {filelist_path}")

    # Prepare Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sources"
    ws.append(["Filename", "File URL (Commons)", "Source URL"])

    processed = 0
    found = 0
    not_found = 0
    missing_pages = 0

    # Process in batches
    for batch_start in range(0, total, BATCH_SIZE):
        batch = titles[batch_start : batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        try:
            data = fetch_wikitext_batch(batch)
        except Exception as e:
            print(f"  ERROR fetching batch {batch_num}: {e}")
            for title in batch:
                ws.append([title, "", f"ERROR: {e}"])
            processed += len(batch)
            time.sleep(DELAY_BETWEEN_BATCHES)
            continue

        # Build a lookup from normalized title to page data
        pages = data.get("query", {}).get("pages", [])
        page_lookup = {}
        for page in pages:
            page_lookup[page.get("title", "")] = page

        for title in batch:
            page = page_lookup.get(title)
            if not page:
                alt_title = title if title.startswith("File:") else f"File:{title}"
                page = page_lookup.get(alt_title)

            if not page or page.get("missing", False):
                ws.append([title, "", "PAGE NOT FOUND"])
                missing_pages += 1
            else:
                file_url = page.get("fullurl", "")
                revisions = page.get("revisions", [])
                wikitext = ""
                if revisions:
                    slots = revisions[0].get("slots", {})
                    main_slot = slots.get("main", {})
                    wikitext = main_slot.get("content", "")

                source = extract_source_from_wikitext(wikitext)
                if source:
                    found += 1
                else:
                    not_found += 1
                    source = ""

                ws.append([title, file_url, source])

            processed += 1

        print(f"  Batch {batch_num}/{total_batches} done — {processed}/{total} processed, {found} sources found")

        # Rate limiting
        if batch_start + BATCH_SIZE < total:
            time.sleep(DELAY_BETWEEN_BATCHES)

    # Auto-size columns (approximate)
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 80)

    wb.save(output_path)
    print(f"\nDone! Results saved to {output_path}")
    print(f"  Total files: {total}")
    print(f"  Sources found: {found}")
    print(f"  No source found: {not_found}")
    print(f"  Missing pages: {missing_pages}")


if __name__ == "__main__":
    main()
