import argparse
from pathlib import Path

from match_and_export import run as run_match
from csv_to_m3u8 import csv_to_m3u8


def main():
    parser = argparse.ArgumentParser(
        description="Recover iTunes playlists and map them to local music files."
    )
    parser.add_argument(
        "library_xml",
        help="Path to iTunes Library.xml file",
    )
    parser.add_argument(
        "music_dir",
        help="Path to local music directory to match against",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Output directory for CSV and playlist files (default: output)",
    )
    parser.add_argument(
        "--csv-only",
        action="store_true",
        help="Only generate the CSV, skip M3U8 generation",
    )
    parser.add_argument(
        "--m3u8-only",
        help="Only generate M3U8 files from an existing CSV (provide CSV path)",
    )
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="Include commented-out entries for missing tracks in M3U8 files",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    csv_path = output_dir / "playlist_mapping.csv"
    playlists_dir = output_dir / "playlists"

    if args.m3u8_only:
        print(f"Generating M3U8 files from: {args.m3u8_only}")
        csv_to_m3u8(args.m3u8_only, str(playlists_dir), args.include_missing)
        return

    run_match(args.library_xml, args.music_dir, str(csv_path))

    if not args.csv_only:
        print()
        csv_to_m3u8(str(csv_path), str(playlists_dir), args.include_missing)

    print()
    print(f"Results in: {output_dir.resolve()}")
    print(f"  CSV:       {csv_path}")
    if not args.csv_only:
        print(f"  Playlists: {playlists_dir}")


if __name__ == "__main__":
    main()
