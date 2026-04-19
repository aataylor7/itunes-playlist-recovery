import os
import re
import unicodedata
from pathlib import Path

AUDIO_EXTENSIONS = {
    ".mp3", ".m4a", ".flac", ".wma", ".ogg", ".aac", ".wav", ".alac", ".aiff",
}


def normalize(text: str) -> str:
    """Normalize a string for fuzzy comparison."""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower().strip()
    text = re.sub(r"[''`]", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_title_from_filename(filename: str) -> str:
    """Strip track number prefix and extension to get a clean title."""
    name = Path(filename).stem
    name = re.sub(r"^\d+[\s._-]+", "", name)
    return name


def scan_music_directory(music_dir: str) -> dict:
    """Walk a music directory and build an index of audio files.

    Returns:
        index: {(normalized_artist, normalized_title): {
            path, artist, title, album, filename
        }}

    Also returns a secondary index keyed only on normalized_title
    for fallback matching.
    """
    primary_index = {}
    title_index = {}

    music_root = Path(music_dir)

    for dirpath, _dirnames, filenames in os.walk(music_root):
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext not in AUDIO_EXTENSIONS:
                continue

            full_path = os.path.join(dirpath, filename)
            if os.path.getsize(full_path) == 0:
                continue
            rel = Path(full_path).relative_to(music_root)
            parts = rel.parts

            if len(parts) >= 3:
                artist = parts[0]
                album = parts[1]
            elif len(parts) == 2:
                artist = parts[0]
                album = ""
            else:
                artist = ""
                album = ""

            title = extract_title_from_filename(filename)
            norm_artist = normalize(artist)
            norm_title = normalize(title)

            entry = {
                "path": full_path,
                "artist": artist,
                "title": title,
                "album": album,
                "filename": filename,
            }

            key = (norm_artist, norm_title)
            if key not in primary_index:
                primary_index[key] = entry

            if norm_title not in title_index:
                title_index[norm_title] = []
            title_index[norm_title].append(entry)

    return primary_index, title_index


if __name__ == "__main__":
    import sys

    music_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    primary, title_idx = scan_music_directory(music_dir)
    print(f"Indexed {len(primary)} files (primary), {len(title_idx)} unique titles")
    for key in list(primary.keys())[:10]:
        print(f"  {key} -> {primary[key]['path']}")
