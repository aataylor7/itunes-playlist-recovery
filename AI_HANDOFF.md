# AI Handoff Document

Context and roadmap for AI assistants continuing work on this project.

## Project Context

This tool was built to recover ~402 playlists from an iTunes Library XML file (iTunes 11.0.4, circa 2007–2022) and map them to ~5,000 local audio files on a Windows machine. The music library lives on an external drive (`E:\music\iTunes Media\Music`) in standard iTunes `Artist/Album/Track` folder structure.

The initial run achieved an **83.7% match rate** (7,309/8,736 playlist entries) using path-based matching only — no ID3 tag reading.

## Current Architecture

The pipeline is intentionally split into discrete, composable steps:

1. `parse_library.py` → Python dicts (tracks + playlists)
2. `scan_local.py` → file index keyed on normalized (artist, title)
3. `match_and_export.py` → CSV (the canonical intermediate format)
4. `csv_to_m3u8.py` → .m3u8 playlist files

The CSV is the central artifact. Any new export format should read from the CSV, not rerun the matching pipeline.

## Known Issues

### False positive fuzzy matches
The title-only fallback in `match_and_export.py` matches on song title alone when there's exactly one local candidate. This produces incorrect matches for common song titles covered by multiple artists. Examples found in the initial run:
- "Louie Louie" by Otis Redding → matched to Kinks version
- "Stand by Me" by Otis Redding → matched to Unknown Artist
- "Lucille" by Otis Redding → matched to BB King
- "You Send Me" by Otis Redding → matched to Sam Cooke

These are flagged as `fuzzy` in the CSV and can be audited, but a smarter fallback strategy would help.

### Normalization edge cases
- Artist names with special characters (`Sly & The Family Stone`, `André Previn`) lose information during normalization
- "The" prefix handling is not implemented — `The Rolling Stones` vs `Rolling Stones` relies on fuzzy threshold
- Compilation albums (Various Artists, Compilations) break the artist-folder assumption

## Roadmap — Future Enhancements

### Priority 1: ID3 tag-based matching (`mutagen`)
**Why:** The current matching is path-only, relying on the folder structure `Artist/Album/Track`. Many files have richer metadata in their ID3/M4A tags (embedded artist, title, album, track number). Reading tags would:
- Improve matches for files in `Unknown Artist` / `Unknown Album` folders
- Resolve false positives by comparing embedded artist metadata
- Handle files that were renamed or reorganized outside iTunes

**How:** Add a `mutagen`-based tag reader in `scan_local.py` that extracts `(artist, title, album)` from audio file tags. Use tag data as the primary index key, falling back to path-derived data when tags are missing. `mutagen` is already in `requirements.txt`.

**Estimated effort:** Small. The scan loop already visits every file — add a `try/except` tag read per file.

### Priority 2: Match confidence tiers
**Why:** The current binary `matched`/`fuzzy`/`missing` status doesn't distinguish between a 0.99 fuzzy score and a 0.86 title-only fallback. Users reviewing the CSV need finer granularity.

**How:** Replace `match_status` with a confidence tier:
- `exact` — normalized artist+title both match perfectly
- `high` — fuzzy score >= 0.95 on both artist and title
- `medium` — fuzzy score >= 0.85, or title-only match with tag-confirmed artist
- `low` — title-only fallback, unconfirmed artist
- `missing` — no match

### Priority 3: Interactive review mode
**Why:** With 1,500+ fuzzy/missing entries, manual CSV review is tedious.

**How:** A simple CLI or TUI (e.g., `rich` or `textual`) that walks through fuzzy matches one at a time, showing the iTunes metadata alongside the matched file's metadata, and lets the user confirm/reject/re-match. Writes corrections back to the CSV.

### Priority 4: Spotify/Apple Music export
**Why:** Many users have migrated to streaming. The CSV already contains artist + title + album, which is enough to search streaming APIs.

**How:** Add export scripts that read the CSV and use:
- Spotify Web API (`spotipy`) to search and create playlists
- Apple Music API (MusicKit) to do the same

This would be a separate module (`csv_to_spotify.py`, `csv_to_apple_music.py`) following the existing pattern.

### Priority 5: Duplicate playlist detection
**Why:** The iTunes library contains several near-duplicate playlists (e.g., multiple "Top 25 Most Played", "Recently Played" snapshots, "andy" / "andy2").

**How:** Compare playlists by track ID overlap. Report clusters of playlists with >80% shared tracks so the user can decide which to keep.

### Priority 6: Missing track acquisition report
**Why:** The 1,427 missing tracks represent music that exists in the playlist metadata but not on disk.

**How:** Generate a separate report (`missing_tracks_report.csv`) with unique missing tracks, de-duped across playlists, sorted by frequency (tracks missing from the most playlists first). This gives the user a prioritized shopping/download list.

## Technical Notes

- The iTunes XML is a standard Apple plist. Python's `plistlib` handles it natively — no XML parsing needed.
- System/smart playlists are filtered out by checking for `Master`, `Distinguished Kind`, and a name blocklist. If Apple adds new system playlist types, the blocklist in `parse_library.py` may need updating.
- The fuzzy match threshold (0.85) is set in `match_and_export.py` as `SIMILARITY_THRESHOLD`. Lowering it increases recall but introduces more false positives.
- M3U8 files use UTF-8 encoding and absolute Windows paths. Relative paths would make them portable across drive letters but would require knowing the playback root at generation time.
