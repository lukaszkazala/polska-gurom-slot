"""Retrieve public metadata and captions for the user-supplied YouTube video."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(tempfile.gettempdir()) / "codex-slot-video-transcript"))
import requests
from youtube_transcript_api import YouTubeTranscriptApi

VIDEO = "BFlRH99TQOw"
OUT = Path(__file__).resolve().parent
URL = f"https://www.youtube.com/watch?v={VIDEO}"


def main():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    match = re.search(r"ytInitialPlayerResponse\s*=\s*", response.text)
    if match is None:
        raise ValueError("Public video metadata unavailable")
    player = json.JSONDecoder().raw_decode(response.text[match.end():])[0]
    details = player.get("videoDetails", {})
    micro = player.get("microformat", {}).get("playerMicroformatRenderer", {})
    api = YouTubeTranscriptApi()
    tracks = api.list(VIDEO)
    track_list = [dict(language=t.language, language_code=t.language_code,
                       is_generated=t.is_generated) for t in tracks]
    chosen = tracks.find_transcript(["en", "pl"])
    fetched = chosen.fetch()
    metadata = {
        "url": URL, "video_id": VIDEO,
        "title": details.get("title"), "author": details.get("author"),
        "channel_id": details.get("channelId"), "duration_seconds": details.get("lengthSeconds"),
        "description": details.get("shortDescription"),
        "publish_date": micro.get("publishDate"), "upload_date": micro.get("uploadDate"),
        "playability_status": player.get("playabilityStatus", {}).get("status"),
        "caption_tracks": track_list,
        "chosen_caption_language": fetched.language_code,
        "chosen_caption_is_generated": fetched.is_generated,
        "caption_segments": len(fetched),
    }
    (OUT / "video_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "transcript.json").write_text(json.dumps(fetched.to_raw_data(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=True, indent=2))
    print("last_caption", fetched[-1])


if __name__ == "__main__":
    main()
