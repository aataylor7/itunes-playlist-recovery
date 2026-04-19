import plistlib
from pathlib import Path


def parse_itunes_library(library_path: str) -> tuple[dict, dict]:
    """Parse an iTunes Library XML file into tracks and playlists.

    Returns:
        tracks: {track_id: {name, artist, album, genre, duration_ms, ...}}
        playlists: {playlist_name: [track_id, ...]}
    """
    path = Path(library_path)
    with open(path, "rb") as f:
        plist = plistlib.load(f)

    tracks = {}
    for track_id_str, track_data in plist.get("Tracks", {}).items():
        track_id = int(track_id_str)
        tracks[track_id] = {
            "track_id": track_id,
            "name": track_data.get("Name", ""),
            "artist": track_data.get("Artist", ""),
            "album_artist": track_data.get("Album Artist", ""),
            "album": track_data.get("Album", ""),
            "genre": track_data.get("Genre", ""),
            "duration_ms": track_data.get("Total Time", 0),
            "track_number": track_data.get("Track Number", 0),
            "year": track_data.get("Year", 0),
        }

    SYSTEM_PLAYLISTS = {
        "Library", "Music", "Movies", "TV Shows", "Podcasts",
        "Purchased", "Genius", "Voice Memos", "Music Videos",
        "Audiobooks", "Videos",
    }

    playlists = {}
    for pl in plist.get("Playlists", []):
        name = pl.get("Name", "")
        if pl.get("Master"):
            continue
        if pl.get("Distinguished Kind") is not None:
            continue
        if name in SYSTEM_PLAYLISTS:
            continue

        track_ids = [item["Track ID"] for item in pl.get("Playlist Items", [])]
        if not track_ids:
            continue

        if name in playlists:
            name = f"{name} ({pl.get('Playlist Persistent ID', 'dup')})"
        playlists[name] = track_ids

    return tracks, playlists


if __name__ == "__main__":
    import sys

    lib_path = sys.argv[1] if len(sys.argv) > 1 else "Library.xml"
    tracks, playlists = parse_itunes_library(lib_path)
    print(f"Parsed {len(tracks)} tracks and {len(playlists)} playlists")
    print(f"\nSample playlists:")
    for name in list(playlists.keys())[:15]:
        print(f"  {name} ({len(playlists[name])} tracks)")
