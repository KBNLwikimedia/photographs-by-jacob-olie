[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![MediaWiki API](https://img.shields.io/badge/API-MediaWiki-006699.svg)](https://www.mediawiki.org/wiki/API:Main_page)
[![Memorix Mediabank API](https://img.shields.io/badge/API-Memorix_Mediabank-orange.svg)](https://webservices.memorix.nl/mediabank/)
[![Wikimedia Commons](https://img.shields.io/badge/Wikimedia-Commons-069.svg)](https://commons.wikimedia.org/wiki/Category:Photographs_by_Jacob_Olie)

# Photographs by Jacob Olie — Wikimedia Commons to Stadsarchief Amsterdam link rot fixer

Tool (3 Python scripts) for fixing outdated, broken source links in 3.600 [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Photographs_by_Jacob_Olie) file pages of photographs by [Jacob Olie](https://en.wikipedia.org/wiki/Jacob_Olie) (1834–1905) to their current source records on the [Stadsarchief Amsterdam Beeldbank](https://archief.amsterdam/beeldbank/).

Jacob Olie was an Amsterdam photographer whose extensive body of work — street scenes, cityscapes, and portraits — is a key visual record of late-19th-century Amsterdam. Over 3,600 of his photographs are available on Wikimedia Commons, with source references pointing to the Stadsarchief Amsterdam collection.

<table>
<tr>
<td><a href="https://archief.amsterdam/beeldbank/detail/81937863-e93c-44c6-05a0-60e9172690d0"><img src="https://images.memorix.nl/ams/thumb/640x480/e1b75a85-93dc-09fd-fee9-c6d3e0d17691.jpg" width="200" alt="Damrak 38-41"></a><br><sub>Damrak 38-41</sub></td>
<td><a href="https://archief.amsterdam/beeldbank/detail/0626a614-7fe5-91fb-0ffc-102c3480d26e"><img src="https://images.memorix.nl/ams/thumb/640x480/86328899-d271-6876-018a-dbc9bb7178a3.jpg" width="200" alt="Keizersgracht"></a><br><sub>Keizersgracht</sub></td>
<td><a href="https://archief.amsterdam/beeldbank/detail/5fadade3-3819-6d6a-4b35-88d71fda2721"><img src="https://images.memorix.nl/ams/thumb/640x480/12d20b8d-dda9-cb95-b6d3-3dbed0e3682c.jpg" width="200" alt="Vondelpark, sneeuwlandschap"></a><br><sub>Vondelpark, sneeuwlandschap</sub></td>
</tr>
<tr>
<td><a href="https://archief.amsterdam/beeldbank/detail/2695b3d1-64ba-9fd5-0c9f-cf4da8d2c06b"><img src="https://images.memorix.nl/ams/thumb/640x480/f7312844-14e6-3ee0-be25-ecd73c3d3284.jpg" width="200" alt="Dam-noordzijde"></a><br><sub>Dam-noordzijde</sub></td>
<td><a href="https://archief.amsterdam/beeldbank/detail/c265965b-ac4c-50a7-3f60-71cdd03f1699"><img src="https://images.memorix.nl/ams/thumb/640x480/e081c848-c7bd-3a5f-7c11-cb945ab5f597.jpg" width="200" alt="Amstel bij Magere Brug"></a><br><sub>Amstel bij Magere Brug</sub></td>
<td><a href="https://archief.amsterdam/beeldbank/detail/94793b47-0002-a64c-66d8-a11485a54ae6"><img src="https://images.memorix.nl/ams/thumb/640x480/7126733f-7d38-0689-aca8-07dd318ecf0c.jpg" width="200" alt="Centraal Station"></a><br><sub>Centraal Station</sub></td>
</tr>
</table>

<sub>Example photographs by Jacob Olie, from the Stadsarchief Amsterdam collection. Click to view on the Beeldbank.</sub>

## What this does

This tool/pipeline can do 3 things:

1) The old Beeldbank URLs (e.g. `http://beeldbank.amsterdam.nl/afbeelding/10019A001542`) embedded in the `{{Photograph}}` templates on Commons ([example](https://commons.wikimedia.org/w/index.php?title=File:%27s-Graveland_Jacob_Olie_(max_res).jpg&action=edit&section=1)) no longer resolve to the correct pages in the Stadsarchief Amsterdam image bank. This pipeline extracts those URLs and resolves them to the new persistent detail page URLs on `beta.archief.amsterdam`.

2) From those new detail pages, 13 descriptive, structured metadata fields are extracted and added to the Excel, see column details below. 

3) This pipeline can easily be adapted for other collections from Stadsarchief Amsterdam, or other Memorix-based archives, see **[MANUAL.md](MANUAL.md)** for detailed usage instructions.

**Input**: a list of Wikimedia Commons filenames (`filelist.txt`)

**Output**: an Excel workbook (`jacob_olie_sources.xlsx`) with 19 columns:

| Column | Content |
|---|---|
| Filename | Commons filename (e.g. `File:Jacob Olie 001.jpg`) |
| File URL (Commons) | Link to the Commons file page |
| Source URL | Original source URL from the `{{Photograph}}` template |
| Archief Amsterdam URL | Transformed search URL on `archief.amsterdam` |
| Archief Amsterdam Detail URL | Canonical detail page URL with UUID |
| Beta Archief Amsterdam Detail URL | Detail page URL on `beta.archief.amsterdam` |
| Titel (dc_title) | Title of the photograph |
| Beschrijving (dc_description) | Description |
| Datering (dc_date) | Date of the photograph |
| Documenttype (sk_documenttype) | Document type (e.g. "foto") |
| Vervaardiger (sk_vervaardiger) | Creator |
| Collectie (dc_provenance) | Collection name |
| Geografische aanduiding (geografische_aanduiding) | Geographic location (street, area) |
| Gebouw (sk_gebouw) | Building name(s) |
| Inventarissen (dc_source) | Link to the archival inventory |
| Afbeeldingsbestand (identifier) | Image file identifier |
| Rechthebbende (sr_rechthebbende) | Rights holder |
| Gebruiksvoorwaarden (sr_leveringsvoorwaarden) | Usage conditions |
| Kwaliteit (quality) | Image quality |

## Quick start

```bash
pip install requests openpyxl

# Step 1: Extract source URLs from Wikimedia Commons
python extract_sources.py

# Step 2: Add transformed Archief Amsterdam search URLs (see MANUAL.md)

# Step 3: Resolve to detail page URLs via the Memorix API
python add_detail_urls.py

# Step 4: Extract full metadata from the Memorix API
python add_metadata.py
```

## Scripts

| Script | Description |
|---|---|
| [`extract_sources.py`](extract_sources.py) | Queries the MediaWiki API to extract source URLs from `{{Photograph}}` templates on Commons file pages. Processes in batches of 50 with rate limiting. |
| [`add_detail_urls.py`](add_detail_urls.py) | Queries the Memorix Mediabank API to resolve Stadsarchief Amsterdam identifiers to detail page UUIDs. |
| [`add_metadata.py`](add_metadata.py) | Queries the Memorix Mediabank API to extract 13 metadata fields (title, date, description, location, etc.) for each record. |

## Documentation

See **[MANUAL.md](MANUAL.md)** for detailed usage instructions, including how to adapt this pipeline for other collections or other Memorix-based archives.

## APIs used

- **[MediaWiki Action API](https://www.mediawiki.org/wiki/API:Main_page)** — to fetch wikitext from Wikimedia Commons (batched, with proper User-Agent)
- **[Memorix Mediabank API](https://webservices.memorix.nl/mediabank/)** by [Vitec](https://www.vitec-memorix.com/) — to resolve record identifiers to UUIDs and extract metadata (public API key, embedded in the Beeldbank page source)

## Rate limiting

Both scripts include rate limiting to be respectful to the servers:
- Wikimedia Commons: 1 second between batches of 50
- Memorix API: 0.5 seconds between individual requests

## License

This repository is dedicated to the public domain under the [CC0 1.0 Universal](LICENSE) license. The photographs by Jacob Olie are in the public domain.
