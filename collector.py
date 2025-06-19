import json
import os
import re
import tempfile
from difflib import SequenceMatcher

import feedparser
import requests
import spotipy
import torch
import whisper
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv


def load_credentials():
    """Load Spotify credentials from environment variables."""
    load_dotenv()  # Load from .env file for local development
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError(
            "Spotify credentials not found. "
            "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your environment "
            "or a .env file."
        )
    return client_id, client_secret


def get_spotify_client():
    """Initializes and returns a Spotipy client."""
    client_id, client_secret = load_credentials()
    if not client_id or not client_secret:
        raise ValueError("Spotify credentials not found.")
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)


def search_spotify_episodes(query, sp, limit=10):
    """Search for podcast episodes on Spotify and return full episode objects."""
    if not query:
        return []
    results = sp.search(q=query, type="episode", limit=limit)
    
    simplified_episodes = results["episodes"]["items"]
    if not simplified_episodes:
        return []

    # From the simplified objects, get the IDs of non-null episodes
    episode_ids = [ep['id'] for ep in simplified_episodes if ep]
    if not episode_ids:
        return []

    # Get the full episode objects in a single API call
    full_episodes_result = sp.episodes(episode_ids)
    
    # The result is a list of full episode objects
    return full_episodes_result['episodes']


def extract_episode_id(spotify_url):
    """Extract episode ID from Spotify URL."""
    match = re.search(r"episode/([a-zA-Z0-9]+)", spotify_url)
    if match:
        return match.group(1)
    raise ValueError("Invalid Spotify episode URL.")


def get_spotify_episode_info(episode_id, sp):
    """Get episode metadata from Spotify."""
    episode = sp.episode(episode_id)
    return {
        "episode_title": episode["name"],
        "show_name": episode["show"]["name"],
        "show_id": episode["show"]["id"],
    }


def search_itunes_podcast(show_name):
    """Find podcast RSS feed via iTunes API."""
    query = show_name.replace(" ", "+")
    url = f"https://itunes.apple.com/search?term={query}&entity=podcast"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data["resultCount"] == 0:
        raise Exception("No podcast found in iTunes search.")

    best_match = max(
        data["results"],
        key=lambda r: SequenceMatcher(
            None, r.get("collectionName", "").lower(), show_name.lower()
        ).ratio(),
        default=None,
    )
    if best_match and "feedUrl" in best_match:
        return best_match["feedUrl"]
    raise Exception("No RSS feed URL found for the podcast.")


def find_episode_in_rss(rss_feed_url, episode_title):
    """Find episode audio URL in RSS feed."""
    feed = feedparser.parse(rss_feed_url)
    best_entry = max(
        feed.entries,
        key=lambda e: SequenceMatcher(
            None, e.get("title", "").lower(), episode_title.lower()
        ).ratio(),
        default=None,
    )
    if (
        best_entry
        and "enclosures" in best_entry
        and best_entry.enclosures
        and SequenceMatcher(
            None, best_entry.title.lower(), episode_title.lower()
        ).ratio()
        > 0.8
    ):
        return best_entry.enclosures[0].get("href")
    raise Exception("Episode not found in the RSS feed.")


def download_audio(audio_url, filename, progress_callback=None):
    """Download audio file with progress."""
    response = requests.get(audio_url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get("content-length", 0))
    with open(filename, "wb") as f:
        if total_size > 0 and progress_callback:
            dl = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    dl += len(chunk)
                    progress_callback(min(1.0, dl / total_size))
        else:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
            if progress_callback:
                progress_callback(1.0)
    return filename


def transcribe_audio(audio_file, model_size="base", progress_callback=None):
    """Transcribe audio using Whisper."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.cuda.empty_cache()

    model = whisper.load_model(model_size, device=device)
    result = model.transcribe(audio_file, verbose=False)

    if progress_callback:
        progress_callback(1.0)
    return result["text"]


def sanitize_filename(name):
    """Sanitize a string to be used as a safe filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name)


def get_transcript_from_url(spotify_url, model_size="base", status_callback=None, progress_callback=None):
    """Full pipeline from Spotify URL to transcription."""
    
    def update_status(msg, progress=None):
        if status_callback:
            status_callback(msg)
        if progress is not None and progress_callback:
            progress_callback(progress)

    update_status("Connecting to Spotify...", 0.05)
    sp = get_spotify_client()

    update_status("Extracting episode information...", 0.1)
    episode_id = extract_episode_id(spotify_url)
    episode_info = get_spotify_episode_info(episode_id, sp)

    update_status("Finding podcast RSS feed...", 0.2)
    rss_feed_url = search_itunes_podcast(episode_info["show_name"])

    update_status("Locating audio file in RSS feed...", 0.3)
    audio_url = find_episode_in_rss(rss_feed_url, episode_info["episode_title"])

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        audio_file = tmp.name
    
    try:
        update_status("Downloading audio file...", 0.4)
        download_audio(audio_url, audio_file, progress_callback=lambda p: update_status("Downloading...", 0.4 + p * 0.3))
        
        update_status("Transcribing audio (this may take a while)...", 0.7)
        transcription = transcribe_audio(
            audio_file, model_size, progress_callback=lambda p: update_status("Transcribing...", 0.7 + p * 0.3)
        )
        
        update_status("Transcription complete!", 1.0)
        return transcription, episode_info

    finally:
        os.remove(audio_file)
        update_status("Cleaning up temporary files.", 1.0)
