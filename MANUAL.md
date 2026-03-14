# Extracting Source URLs from Wikimedia Commons to Stadsarchief Amsterdam Beeldbank

This manual documents a two-step pipeline for linking Wikimedia Commons file pages to their original source records on the [Stadsarchief Amsterdam Beeldbank](https://archief.amsterdam/beeldbank/).

## Overview

Many photographs on Wikimedia Commons that originate from the Stadsarchief Amsterdam use the `{{Photograph}}` template, which includes a `source` field pointing to the old Beeldbank URL (e.g. `http://beeldbank.amsterdam.nl/afbeelding/10019A001542`). The old Beeldbank has been replaced by a new platform at `archief.amsterdam`, which uses different URLs based on internal UUIDs.

This pipeline:

1. **Extracts** the source URL from each Commons file page (`extract_sources.py`)
2. **Transforms** old `beeldbank.amsterdam.nl` URLs into new `archief.amsterdam` search URLs (inline in the Excel)
3. **Resolves** each search URL to the canonical detail page URL via the Memorix API (`add_detail_urls.py`)

## Prerequisites

- Python 3.8+
- Required packages:
  ```
  pip install requests openpyxl
  ```

## Pipeline steps

### Step 1: Prepare `filelist.txt`

Create a plain text file called `filelist.txt` with one Wikimedia Commons filename per line, including the `File:` prefix:

```
File:Jacob Olie 001.jpg
File:Jacob Olie 002.jpg
File:Vijgendam Jacob Olie 004.jpg
```

You can generate this list from a Commons category using tools like [PetScan](https://petscan.wmcloud.org/) or the [MediaWiki API](https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Photographs_by_Jacob_Olie&cmtype=file&cmlimit=500&format=json).

### Step 2: Extract source URLs from Commons

Run:

```
python extract_sources.py
```

This will:
- Read all filenames from `filelist.txt`
- Query the MediaWiki API in batches of 50 (with 1s delay between batches)
- Parse the `{{Photograph}}` template to extract the `source` parameter value
- Write the results to `jacob_olie_sources.xlsx` with columns:
  - **A — Filename**: the Commons filename
  - **B — File URL (Commons)**: full URL to the Commons file page
  - **C — Source URL**: the extracted source URL (typically a `beeldbank.amsterdam.nl` link)

**Runtime**: ~1.5 minutes for 3600 files.

### Step 3: Transform old Beeldbank URLs to new search URLs

This step adds a column D with the equivalent `archief.amsterdam` search URL. You can do this manually in the Excel with a formula, or with a short Python snippet. The transformation is:

| Old URL pattern | Identifier example |
|---|---|
| `http://beeldbank.amsterdam.nl/afbeelding/10019AXXXXXX` | `10019A001542` |
| `http://beeldbank.amsterdam.nl/afbeelding/010019XXXXXX` | `010019000001` |
| `http://beeldbank.amsterdam.nl/afbeelding/BXXXXXXX` | `BMAB00003000001` |

The new search URL format is:
```
https://archief.amsterdam/beeldbank/?mode=gallery&view=horizontal&q={IDENTIFIER}&rows=1&page=1
```

Where `{IDENTIFIER}` is the part after `/afbeelding/` in the old URL.

**Python snippet** (already applied in our workflow):
```python
import re, openpyxl

wb = openpyxl.load_workbook('jacob_olie_sources.xlsx')
ws = wb.active
ws.cell(row=1, column=4, value='Archief Amsterdam URL')

pattern = re.compile(
    r'https?://beeldbank\.amsterdam\.nl/afbeelding/(10019A\w+|010019\w+|B\w+)'
)

for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    source_url = row[2].value or ''
    m = pattern.search(source_url)
    if m:
        identifier = m.group(1)
        row[0].offset(column=3).value = (
            f'https://archief.amsterdam/beeldbank/'
            f'?mode=gallery&view=horizontal&q={identifier}&rows=1&page=1'
        )

wb.save('jacob_olie_sources.xlsx')
```

### Step 4: Resolve to canonical detail page URLs

Run:

```
python add_detail_urls.py
```

This will:
- Read column D ("Archief Amsterdam URL") from the Excel
- Extract the identifier from each URL's `q=` parameter
- Query the **Memorix Mediabank API** to find the record's internal UUID
- Construct the detail page URL: `https://archief.amsterdam/beeldbank/detail/{UUID}`
- Write the result to column E ("Archief Amsterdam Detail URL")

**Runtime**: ~30 minutes for 3600 files (0.5s delay per request).

## Final Excel structure

| Column | Header | Example |
|---|---|---|
| A | Filename | `File:Jacob Olie 001.jpg` |
| B | File URL (Commons) | `https://commons.wikimedia.org/wiki/File:Jacob_Olie_001.jpg` |
| C | Source URL | `http://beeldbank.amsterdam.nl/afbeelding/010019000001` |
| D | Archief Amsterdam URL | `https://archief.amsterdam/beeldbank/?mode=gallery&view=horizontal&q=010019000001&rows=1&page=1` |
| E | Archief Amsterdam Detail URL | `https://archief.amsterdam/beeldbank/detail/bf2bc41b-9441-9049-1f28-5012c8617cc3` |

## Adapting for other collections

### Other Stadsarchief Amsterdam identifiers

If the source URLs use a different identifier pattern (not `10019A`, `010019`, or `B`), update the regex in step 3 to match. The Memorix API lookup in step 4 works with any Stadsarchief Amsterdam identifier — no changes needed there.

### Other Memorix-based archives

Many Dutch archives use Vitec Memorix. To adapt this workflow:

1. **Find the API key**: Visit the archive's Beeldbank page, view page source, and look for a `<pic-mediabank>` HTML element with `data-api-key` and `data-api-url` attributes:
   ```html
   <pic-mediabank
       data-api-key="eb37e65a-eb47-11e9-b95c-60f81db16c0e"
       data-api-url="https://webservices.memorix.nl/mediabank/"
   />
   ```

2. **Update `add_detail_urls.py`**:
   - Set `API_KEY` to the value from `data-api-key`
   - Set `API_URL` to `{data-api-url}media` (append `media` to the base URL)
   - Set `DETAIL_BASE` to the archive's detail page base URL (e.g. `https://example-archive.nl/beeldbank/detail/`)

3. **Update the source URL regex** (step 3) to match the URL patterns used by the other archive.

### The Memorix Mediabank API

The API endpoint is:

```
GET https://webservices.memorix.nl/mediabank/media?q={query}&rows={n}&page={p}&apiKey={key}
```

The response is JSON with the following structure:

```json
{
  "metadata": {
    "pagination": { "total": 1, "rows": 1, "currentPage": 1, "pages": 1 }
  },
  "media": [
    {
      "id": "bf2bc41b-9441-9049-1f28-5012c8617cc3",
      "title": "Amstel 51-55 enz. (v.l.n.r.)",
      "description": "Gezien in noordelijke richting ...",
      "asset": [
        {
          "uuid": "d46023d7-b5ec-c557-39d8-af463e01a3b0",
          "thumb": {
            "small": "https://images.memorix.nl/ams/thumb/350x350crop/...",
            "large": "https://images.memorix.nl/ams/thumb/640x480/..."
          }
        }
      ],
      "metadata": [ ... ]
    }
  ]
}
```

Key fields:
- `media[0].id` — the record UUID, used in the detail page URL
- `media[0].asset[0].thumb` — thumbnail image URLs at various sizes
- `media[0].title` / `media[0].description` — record metadata

## Rate limiting and etiquette

- **Wikimedia Commons API** (step 2): batches of 50, 1 second between batches. See the [API etiquette guidelines](https://www.mediawiki.org/wiki/API:Etiquette).
- **Memorix API** (step 4): 1 request per 0.5 seconds. There is no documented rate limit, so we err on the side of caution.
- Both scripts set a descriptive `User-Agent` header that identifies the project, as required by Wikimedia and good practice for any API.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `PermissionError` when saving Excel | The `.xlsx` file is open in Excel | Close the file in Excel before running the script |
| Source URL is empty | The Commons page doesn't use the `{{Photograph}}` template | Check the page manually; it may use `{{Information}}` or `{{Artwork}}` instead |
| "NOT FOUND" in detail URL column | The identifier returned no results from the Memorix API | The record may have been removed or the identifier may not match; verify manually on the Beeldbank website |
| `HTTPError 429` | Too many requests | Increase the `DELAY` value in the script |

## Scripts reference

| Script | Purpose |
|---|---|
| `extract_sources.py` | Step 2 — Extract source URLs from Wikimedia Commons `{{Photograph}}` templates |
| `add_detail_urls.py` | Step 4 — Resolve identifiers to Beeldbank detail page URLs via the Memorix API |
