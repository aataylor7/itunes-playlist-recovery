# iTunes Playlist Recovery

Recover playlists from an iTunes Library XML file and map them to a local music collection. Outputs a master CSV of all playlist-track mappings and generates player-agnostic `.m3u8` playlist files.

## Why

iTunes Library XML files contain a complete record of every playlist and track, but the data is locked in Apple's plist format and tied to file paths from the original machine. This tool extracts that data, matches it against music files on your current machine, and produces portable playlist files that work with Groove Music, VLC, foobar2000, Winamp, and any other player that supports M3U.

## How It Works

1. **Parse** — Reads the iTunes XML using Python's `plistlib`. Extracts all track metadata (artist, title, album, genre, duration, year) and all user-created playlists with their track listings.
2. **Scan** — Walks your local music directory, indexing audio files by artist and title (derived from the folder structure: `Artist/Album/Track`).
3. **Match** — Maps iTunes tracks to local files using a two-pass strategy:
   - **Exact match** on normalized (artist, title)
   - **Fuzzy match** using `difflib.SequenceMatcher` with a configurable similarity threshold (default 0.85)
   - **Title-only fallback** when a title has exactly one local candidate
4. **Export CSV** — Writes a master CSV with every playlist-track entry, local file path, and match status (`matched`, `fuzzy`, or `missing`).
5. **Generate M3U8** — Converts the CSV into one `.m3u8` file per playlist, with optional commented entries for missing tracks.

## Requirements

- Python 3.10+
- No external dependencies for core functionality

## Usage

### Full pipeline (CSV + M3U8 playlists)

```bash
python main.py "path/to/Library.xml" "path/to/music/folder"
```

### CSV only

```bash
python main.py "path/to/Library.xml" "path/to/music/folder" --csv-only
```

### M3U8 from existing CSV

```bash
python main.py "path/to/Library.xml" "path/to/music/folder" --m3u8-only output/playlist_mapping.csv
```

### Include missing tracks as comments in M3U8 files

```bash
python main.py "path/to/Library.xml" "path/to/music/folder" --include-missing
```

### Custom output directory

```bash
python main.py "path/to/Library.xml" "path/to/music/folder" -o my_output
```

### Run individual modules

```bash
# Parse library only
python parse_library.py "path/to/Library.xml"

# Scan local music only
python scan_local.py "path/to/music/folder"

# Match and export CSV
python match_and_export.py "path/to/Library.xml" "path/to/music/folder" output.csv

# Convert CSV to M3U8
python csv_to_m3u8.py output/playlist_mapping.csv output/playlists --include-missing
```

## Output

```
output/
├── playlist_mapping.csv    # Master CSV with all playlist-track mappings
└── playlists/              # One .m3u8 file per playlist
    ├── 60's Music.m3u8
    ├── Tool, Lateralus.m3u8
    ├── the drive.m3u8
    └── ...
```

### CSV columns

| Column | Description |
|--------|-------------|
| `playlist` | Playlist name |
| `position` | Track position within the playlist |
| `track_name` | Song title |
| `artist` | Artist name |
| `album` | Album name |
| `genre` | Genre |
| `duration_ms` | Duration in milliseconds |
| `year` | Release year |
| `local_path` | Matched local file path (empty if missing) |
| `match_status` | `matched`, `fuzzy`, or `missing` |
| `match_method` | `exact`, `score=X.XX`, or empty |

## Project Structure

```
├── main.py              # CLI entry point — orchestrates the full pipeline
├── parse_library.py     # iTunes XML parser (plistlib-based)
├── scan_local.py        # Local music directory scanner and indexer
├── match_and_export.py  # Track matching engine and CSV exporter
├── csv_to_m3u8.py       # CSV-to-M3U8 playlist generator
├── requirements.txt
└── .gitignore
```

## License

MIT
