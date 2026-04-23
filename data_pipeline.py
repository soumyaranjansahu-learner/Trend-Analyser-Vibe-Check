import os
import requests
import billboard
from database import SessionLocal, init_db
from models import Track, DailySnapshot
from classifier import get_audio_features, extract_lyric_emotion, map_to_vibe

def calculate_trend_score(rank: int, max_rank: int = 50, previous_rank: int = None) -> float:
    rank_score = (max_rank - rank) / max_rank
    velocity = 0.0
    if previous_rank:
        velocity = (previous_rank - rank) / max_rank 
    velocity = max(0.0, min(1.0, velocity + 0.5)) 
    return (rank_score * 0.6) + (velocity * 0.4)

def fetch_billboard_hot_100():
    try:
        chart = billboard.ChartData('hot-100')
        return [{"title": item.title, "artist": item.artist, "rank": item.rank} for item in chart[:10]]
    except Exception as e:
        print(f"Failed to fetch Billboard: {e}")
        return []

def get_itunes_preview(title, artist):
    try:
        query = f"{title} {artist}"
        url = f"https://itunes.apple.com/search?term={requests.utils.quote(query)}&entity=song&limit=1"
        res = requests.get(url, timeout=5).json()
        if res['results']:
            track = res['results'][0]
            return {
                "id": str(track.get('trackId', title)),
                "preview_url": track.get('previewUrl'),
                "genre": track.get('primaryGenreName', 'Pop')
            }
    except Exception as e:
        pass
    return {"id": title.replace(" ", "_"), "preview_url": None, "genre": "Pop"}

def get_lyrics(title, artist):
    try:
        # Simplify artist name to increase matches 
        artist_clean = artist.split(' Featuring ')[0].split(' & ')[0]
        url = f"https://api.lyrics.ovh/v1/{requests.utils.quote(artist_clean)}/{requests.utils.quote(title)}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json().get('lyrics')
    except Exception:
        pass
    return None

def derive_valence_from_emotion(emotion: str) -> float:
    mapping = {
        "joy": 0.9, "love": 0.8, "surprise": 0.6,
        "neutral": 0.5, "anger": 0.3, "fear": 0.2, "sadness": 0.1
    }
    return mapping.get(emotion, 0.5)

def run_pipeline():
    print("Starting VIBE-CHECK Keyless Data Pipeline...")
    db = SessionLocal()
    init_db()

    print("Fetching Billboard Hot 100...")
    tracks = fetch_billboard_hot_100()
    if not tracks:
        print("Could not fetch charting tracks.")
        return

    for idx, item in enumerate(tracks):
        title = item['title']
        artist = item['artist']
        bb_rank = item['rank']
        
        print(f"Processing #{idx+1}: {title} by {artist}")

        itunes_data = get_itunes_preview(title, artist)
        track_id = itunes_data['id']
        
        track = db.query(Track).filter(Track.id == track_id).first()
        
        if not track:
            # 1. Fetch iTunes audio features
            librosa_features = get_audio_features(itunes_data['preview_url'])
            bpm = librosa_features['bpm'] or 120.0
            energy = librosa_features['energy'] or 0.6
            key = librosa_features['key'] or 0
            
            # 2. Fetch Lyrics
            lyrics = get_lyrics(title, artist)
            if not lyrics:
                lyrics = "[Lyrics not found on OVH]"
                
            # 3. Classify Lyrics Emotion
            lyric_emotion = extract_lyric_emotion(lyrics)
            
            # 4. Derive Valence
            valence = derive_valence_from_emotion(lyric_emotion)
            
            # 5. Combined Multi-Modal Vibe
            combined = map_to_vibe({"energy": energy}, lyric_emotion, valence)

            track = Track(
                id=track_id,
                title=title,
                artist=artist,
                genre=itunes_data['genre'],
                bpm=bpm,
                energy=energy,
                key=key,
                valence=valence,
                lyrics=lyrics,
                lyric_emotion=lyric_emotion,
                combined_emotion=combined
            )
            db.add(track)
            db.commit()
            db.refresh(track)

        # Create Daily Snapshot
        last_snap = db.query(DailySnapshot).filter(DailySnapshot.track_id == track_id)\
                                           .order_by(DailySnapshot.date.desc()).first()
        prev_rank = last_snap.billboard_hot_100_rank if last_snap else bb_rank
        
        t_score = calculate_trend_score(rank=bb_rank, max_rank=100, previous_rank=prev_rank)
        
        snapshot = DailySnapshot(
            track_id=track_id,
            spotify_viral_rank=None, # Deprecated in keyless mode
            billboard_hot_100_rank=bb_rank,
            social_velocity=float((prev_rank - bb_rank) / 100.0),
            trend_weight_score=t_score
        )
        db.add(snapshot)
    
    db.commit()
    db.close()
    print("Data Pipeline Completed.")

if __name__ == "__main__":
    run_pipeline()
