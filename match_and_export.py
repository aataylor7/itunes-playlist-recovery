import csv
from difflib import SequenceMatcher
from pathlib import Path

from parse_library import parse_itunes_library
from scan_local import normalize, scan_music_directory

SIMILARITY_THRESHOLD = 0.85


def fuzzy_match(s1: str, s2: str) -> float:
    return SequenceMatcher(None, s1, s2).ratio()


def match_tracks(
    tracks: dict,
    playlists: dict,
    primary_index: dict,
    title_index: dict,
) -> list[dict]:
    """Match iTunes playlist tracks to local files.

    Returns a list of row dicts ready for CSV export.
    """
    rows = []

    for playlist_name, track_ids in playlists.items():
        for position, track_id in enumerate(track_ids, 1):
            track = tracks.get(track_id)
            if not track:
                continue

            norm_artist = normalize(track["artist"])
            norm_title = normalize(track["name"])

            local_path = ""
            match_status = "missing"
            match_method = ""

            exact_key = (norm_artist, norm_title)
            if exact_key in primary_index:
                local_path = primary_index[exact_key]["path"]
                match_status = "matched"
                match_method = "exact"
            else:
                best_score = 0.0
                best_entry = None

                for key, entry in primary_index.items():
                    idx_artist, idx_title = key
                    title_score = fuzzy_match(norm_title, idx_title)
                    if title_score < SIMILARITY_THRESHOLD:
                        continue
                    artist_score = fuzzy_match(norm_artist, idx_artist)
                    if artist_score < SIMILARITY_THRESHOLD:
                        continue
                    combined = (title_score + artist_score) / 2
                    if combined > best_score:
                        best_score = combined
                        best_entry = entry

                if best_entry is None and norm_title in title_index:
                    candidates = title_index[norm_title]
                    if len(candidates) == 1:
                        best_entry = candidates[0]
                        best_score = 1.0

                if best_entry and best_score >= SIMILARITY_THRESHOLD:
                    local_path = best_entry["path"]
                    match_status = "fuzzy"
                    match_method = f"score={best_score:.2f}"

            rows.append({
                "playlist": playlist_name,
                "position": position,
                "track_name": track["name"],
                "artist": track["artist"],
                "album": track["album"],
                "genre": track["genre"],
                "duration_ms": track["duration_ms"],
                "year": track["year"],
                "local_path": local_path,
                "match_status": match_status,
                "match_method": match_method,
            })

    return rows


def export_csv(rows: list[dict], output_path: str):
    fieldnames = [
        "playlist", "position", "track_name", "artist", "album",
        "genre", "duration_ms", "year", "local_path",
        "match_status", "match_method",
    ]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(library_path: str, music_dir: str, output_csv: str) -> list[dict]:
    print(f"Parsing iTunes library: {library_path}")
    tracks, playlists = parse_itunes_library(library_path)
    print(f"  Found {len(tracks)} tracks in {len(playlists)} playlists")

    print(f"Scanning local music: {music_dir}")
    primary_index, title_index = scan_music_directory(music_dir)
    print(f"  Indexed {len(primary_index)} local files")

    print("Matching tracks...")
    rows = match_tracks(tracks, playlists, primary_index, title_index)

    matched = sum(1 for r in rows if r["match_status"] != "missing")
    total = len(rows)
    print(f"  {matched}/{total} track-playlist entries matched ({matched/total*100:.1f}%)")

    print(f"Exporting CSV: {output_csv}")
    export_csv(rows, output_csv)
    print("Done.")

    return rows


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python match_and_export.py <library.xml> <music_dir> [output.csv]")
        sys.exit(1)

    lib = sys.argv[1]
    music = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else "output/playlist_mapping.csv"
    run(lib, music, out)
