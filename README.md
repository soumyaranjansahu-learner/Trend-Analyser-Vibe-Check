# VIBE-CHECK MVP

Vibe-Check is a production-ready Minimum Viable Product (MVP) dashboard designed to track daily trending music categorized by Emotion and Genre. It uses a Multi-Modal Emotion Engine that parses both the sonic characteristics (Energy/BPM) and the lyrical sentiments of trending tracks from Spotify and Billboard.

## 📈 Business Value

For record labels, A&R delegates, and music marketers, tracking just the "Top 50" is no longer actionable. Understanding the *why* and the *mood* of the cultural zeitgeist is what drives profitable decision-making.

By using the Vibe-Check Dashboard:
1. **Identify Emerging Emotional Shifts**: Before a genre takes off, the underlying *mood* shifts. Spotting a sudden uptick in "Aggressive Hip-Hop" or "Melancholic Pop" reveals societal trends.
2. **Actionable Sub-Genre Discovery**: Filter out the noise and view only songs matching an emotional profile to discover overlapping, rising sub-genres.
3. **Data-Driven Signings**: A&R can prioritize signing talent that fits the ascendant emotional profiles in standard viral playlists. 
4. **Marketing Resonance**: Ad placements and playlist curation can be aligned with the daily "Global Vibe Shift," maximizing user engagement.

## 🏗 Architecture

1. **Data Ingestion**: Connected via the `spotipy` API. Fetches the 'Spotify Viral 50', augmented by mapping against the Billboard Hot 100 rankings. 
2. **Multi-Modal Emotion Engine**:
   - **Audio Analysis (`librosa`)**: Downloads a 30-second Spotify preview (fallback to generic Spotify properties if blocked) to calculate BPM, Key, and Energy natively. Maps these to the Russell Circumplex Model of Affect (Arousal vs. Valence).
   - **Lyrics Analysis (`transformers`)**: Incorporates HuggingFace's `distilbert-base-uncased-emotion` NLP pipeline. Identifies if the song leans Joy, Sadness, Anger, Fear, Surprise, or Love.
3. **Database Layer**: Leverages SQLAlchemy ORM for relational storage of `Tracks` and `DailySnapshots` (calculating Velocity). Built to plug directly into PostgreSQL but defaults to SQLite for local MVP friction-less starting.
4. **Frontend Dashboard**: A `Streamlit` application utilizing `Plotly` graphs to render dark-mode UI charts mapping the Daily Vibe Shifts.

## 🚀 Setup & Execution

### 1. Environment Variables
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Provide your `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET`. Without these, data ingestion will fail. 
(Optional) provide `GENIUS_ACCESS_TOKEN` for real lyrics extraction.

### 2. Install Requirements
Ensure you are using python 3.10+
```bash
pip install -r requirements.txt
```

### 3. Run Data Pipeline (Ingestion)
This fetches the latest Spotify Viral 50, processes audio via Librosa and HuggingFace, and populates the database.
```bash
python data_pipeline.py
```

### 4. Boot the Dashboard
```bash
streamlit run app.py
```
