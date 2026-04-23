import os
import requests
import tempfile
import librosa
import numpy as np
# We instantiate the pipeline once so it stays in memory after the first load.
# This classification model returns 'joy', 'sadness', 'anger', 'fear', 'surprise', 'love'
try:
    from transformers import pipeline
    print("Loading HuggingFace emotion pipeline...")
    emotion_classifier = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion", return_all_scores=False)
except Exception as e:
    print(f"Warning: Could not load HuggingFace model. Error: {e}")
    emotion_classifier = None

def get_audio_features(preview_url: str):
    """
    Downloads an mp3 preview from Spotify, uses Librosa to analyze BPM, Key, and Energy.
    Fallback to mocked data/None if preview not available or fails.
    """
    if not preview_url:
        return {"bpm": None, "energy": None, "key": None}

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".m4a")
    try:
        # Download the preview
        response = requests.get(preview_url)
        response.raise_for_status()
        with open(temp_file.name, "wb") as f:
            f.write(response.content)

        # Load with Librosa
        y, sr = librosa.load(temp_file.name, sr=None)

        # Tempo (BPM)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Energy (RMS)
        rms = librosa.feature.rms(y=y)
        energy_score = float(np.mean(rms)) * 10 # Scale up slightly for visualization
        
        # Key (Using chroma)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_idx = int(np.argmax(np.mean(chroma, axis=1))) # 0-11 representing C, C#, D etc.

        return {
            "bpm": float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo),
            "energy": min(energy_score, 1.0), # cap at 1.0
            "key": key_idx
        }

    except Exception as e:
        print(f"Error processing audio features from {preview_url}: {e}")
        return {"bpm": None, "energy": None, "key": None}
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)

def extract_lyric_emotion(lyrics: str) -> str:
    """
    Uses HF distilbert-base-uncased-emotion to classify lyrics.
    Limits the text length to avoid token limits.
    """
    if not lyrics or emotion_classifier is None:
        return "neutral"
    
    # Truncate string to avoid "sequence length too long" errors
    # Approximately 512 tokens. A safe character limit is around 1500 max.
    truncated_lyrics = lyrics[:1500] 
    
    try:
        results = emotion_classifier(truncated_lyrics)
        if results and len(results) > 0:
            return results[0]['label']
    except Exception as e:
        print(f"Error classifying lyrics: {e}")
        
    return "neutral"

def map_to_vibe(audio_features: dict, lyric_emotion: str, valence: float = 0.5) -> str:
    """
    Maps Arousal vs Valence (Russell Circumplex) + Lyric Emotion into a single Vibe Tag.
    Valence is taken from Spotify's own features (easier than Librosa audio feature derivation) or defaulted to 0.5.
    Arousal can be mapped from Librosa Energy.
    """
    arousal = audio_features.get("energy") or 0.5
    
    # Simple mapping
    if arousal > 0.6 and valence > 0.6:
        base_vibe = "Energetic & Happy"
    elif arousal > 0.6 and valence <= 0.6:
        base_vibe = "Aggressive/Tense"
    elif arousal <= 0.6 and valence > 0.6:
        base_vibe = "Chill & Cheerful"
    else:
        base_vibe = "Somber/Melancholy"
        
    if lyric_emotion and lyric_emotion != "neutral":
        return f"{base_vibe} ({str(lyric_emotion).title()} Lyrics)"
    
    return base_vibe

if __name__ == "__main__":
    # Test stub
    test_lyrics = "'Cause I'm so happy, clapping along"
    print("Test lyrics emotion:", extract_lyric_emotion(test_lyrics))
