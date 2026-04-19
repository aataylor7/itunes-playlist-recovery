import csv
import re
from collections import defaultdict
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Make a playlist name safe for use as a filename."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"_+", "_", name).strip("_ ")
    if len(name) > 200:
        name = name[:200]
    return name


def csv_to_m3u8(csv_path: str, output_dir: str, include_missing: bool = False):
    """Read a playlist CSV and generate one .m3u8 file per playlist.

    Args:
        csv_path: Path to the playlist_mapping.csv
        output_dir: Directory to write .m3u8 files into
        include_missing: If True, include commented-out lines for missing tracks
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    playlists = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            playlists[row["playlist"]].append(row)

    created = 0
    skipped = 0

    for name, tracks in playlists.items():
        tracks.sort(key=lambda r: int(r["position"]))

        matched_tracks = [t for t in tracks if t["match_status"] != "missing"]
        if not matched_tracks and not include_missing:
            skipped += 1
            continue

        safe_name = sanitize_filename(name)
        m3u_path = out / f"{safe_name}.m3u8"

        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")

            for track in tracks:
                is_missing = track["match_status"] == "missing"
                if is_missing and not include_missing:
                    continue

                duration_s = int(int(track["duration_ms"]) / 1000) if track["duration_ms"] else -1
                artist = track["artist"]
                title = track["track_name"]
                extinf = f"#EXTINF:{duration_s},{artist} - {title}"
                path_line = track["local_path"]

                if is_missing:
                    f.write(f"# MISSING: {artist} - {title}\n")
                    f.write(f"# {extinf}\n")
                else:
                    f.write(f"{extinf}\n")
                    f.write(f"{path_line}\n")

        created += 1

    print(f"Created {created} playlist files in {output_dir}")
    if skipped:
        print(f"Skipped {skipped} playlists (no matched tracks)")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python csv_to_m3u8.py <playlist_mapping.csv> [output_dir] [--include-missing]")
        sys.exit(1)

    csv_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "output/playlists"
    include_missing = "--include-missing" in sys.argv
    csv_to_m3u8(csv_path, output_dir, include_missing)
