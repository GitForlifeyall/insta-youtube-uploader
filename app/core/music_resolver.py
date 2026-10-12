"""
🎵 Instagram Music & Audio Track Resolver
Extracts and resolves official Instagram audio tracks from:
1. Direct Instagram audio URLs (e.g. https://www.instagram.com/reels/audio/1711245173277332?exln=OGVtZnlpand0aHJt)
2. Direct audio cluster IDs or asset IDs (e.g. 1711245173277332)
3. Catalogue search queries (e.g. 'Starboy The Weeknd')
"""

import re
import logging
from typing import Optional, List, Dict, Any
from instagrapi.extractors import extract_track

logger = logging.getLogger("music_resolver")


def extract_audio_id_from_query(query: Optional[str]) -> Optional[str]:
    """
    Extracts the numeric audio cluster ID or audio asset ID from URLs or strings.
    Examples matched:
    - https://www.instagram.com/reels/audio/1711245173277332?exln=OGVtZnlpand0aHJt -> 1711245173277332
    - https://instagram.com/audio/1711245173277332/ -> 1711245173277332
    - reels/audio/1711245173277332 -> 1711245173277332
    - audio_cluster_id=1711245173277332 -> 1711245173277332
    - 1711245173277332 -> 1711245173277332
    """
    if not query:
        return None
    cleaned = str(query).strip()

    # 1. Regex for audio URL paths
    match = re.search(
        r'(?:reels/audio/|audio/|audio_cluster_id[=:]\s*|audio_asset_id[=:]\s*|track_id[=:]\s*)(\d+)',
        cleaned,
        re.IGNORECASE
    )
    if match:
        return match.group(1)

    # 2. Pure digits ID string
    if cleaned.isdigit() and len(cleaned) >= 6:
        return cleaned

    return None


def resolve_music_track(cl, query: Optional[str], cluster_id: Optional[str] = None):
    """
    Resolves an official Instagram Track object from either an audio URL, cluster ID, or query.
    Returns: instagrapi Track object, or None if unresolved.
    """
    target_id = extract_audio_id_from_query(query) or (str(cluster_id).strip() if cluster_id else None)

    if target_id:
        logger.info(f"Target audio ID extracted: {target_id}")

        # 1. Try track_info_by_canonical_id first (standard for Instagram audio URLs & cluster IDs)
        try:
            raw = cl.track_info_by_canonical_id(target_id)
            if hasattr(raw, "title") and getattr(raw, "title", None):
                logger.info(f"Resolved track via track_info_by_canonical_id: {raw.title} by {getattr(raw, 'display_artist', '')}")
                return raw
            if isinstance(raw, dict):
                track_data = (
                    raw.get("track")
                    or raw.get("audio_info")
                    or raw.get("metadata", {}).get("music_info", {}).get("music_asset_info")
                    or raw.get("metadata", {}).get("music_info")
                )
                if track_data:
                    return extract_track(track_data)
        except Exception as e:
            logger.debug(f"track_info_by_canonical_id lookup failed for {target_id}: {e}")

        # 2. Try track_info_by_id
        try:
            raw = cl.track_info_by_id(target_id)
            if hasattr(raw, "title") and getattr(raw, "title", None):
                logger.info(f"Resolved track via track_info_by_id: {raw.title} by {getattr(raw, 'display_artist', '')}")
                return raw
            if isinstance(raw, dict):
                track_data = (
                    raw.get("track")
                    or raw.get("audio_info")
                    or raw.get("metadata", {}).get("music_info", {}).get("music_asset_info")
                    or raw.get("metadata", {}).get("music_info")
                )
                if track_data:
                    return extract_track(track_data)
        except Exception as e:
            logger.debug(f"track_info_by_id lookup failed for {target_id}: {e}")

        # 3. Try searching catalogue by ID - ONLY return if ID strictly matches!
        try:
            tracks = cl.search_music(target_id)
            if tracks:
                for t in tracks:
                    if (
                        str(getattr(t, "audio_cluster_id", "")) == target_id
                        or str(getattr(t, "id", "")) == target_id
                        or str(getattr(t, "audio_asset_id", "")) == target_id
                    ):
                        logger.info(f"Resolved track via search_music ID match: {t.title} by {getattr(t, 'display_artist', '')}")
                        return t
        except Exception as e:
            logger.debug(f"search_music by ID failed for {target_id}: {e}")

    # Standard textual search if not a direct URL/ID
    if query and not query.startswith("http") and not (target_id and query.strip() == target_id):
        try:
            tracks = cl.search_music(query)
            if tracks:
                logger.info(f"Resolved track via keyword search '{query}': {tracks[0].title} by {getattr(tracks[0], 'display_artist', '')}")
                return tracks[0]
        except Exception as e:
            logger.warning(f"search_music failed for query '{query}': {e}")

    return None


def search_music_tracks(cl, query: str):
    """
    Searches or resolves tracks from a query. If query is a direct audio URL or ID,
    returns the exact resolved track wrapped in a list. Otherwise, returns catalogue search results.
    """
    target_id = extract_audio_id_from_query(query)
    if target_id:
        single = resolve_music_track(cl, query=target_id)
        if single:
            return [single]

    # Standard keyword search
    clean_query = query.strip()
    return cl.search_music(clean_query)
