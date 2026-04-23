from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Track, DailySnapshot
import pandas as pd
from data_pipeline import run_pipeline
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB synchronously so tables exist immediately
    init_db()
    
    # Run the data pipeline in the background so the app can start serving immediately
    def start_pipeline():
        try:
            print("Running initial background data pipeline...")
            run_pipeline()
        except Exception as e:
            print(f"Background pipeline failed: {e}")
            
    threading.Thread(target=start_pipeline, daemon=True).start()
    yield
    print("Shutting down VIBE-CHECK API")

app = FastAPI(title="VIBE-CHECK API", lifespan=lifespan)

# Setup CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/dashboard")
def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Returns the core data needed for the VIBE-CHECK dashboard visualization.
    """
    try:
        query = db.query(
            Track.id,
            Track.title, 
            Track.artist, 
            Track.genre, 
            Track.combined_emotion, 
            Track.lyric_emotion,
            Track.bpm,
            Track.energy,
            Track.valence,
            DailySnapshot.spotify_viral_rank,
            DailySnapshot.trend_weight_score,
            DailySnapshot.date
        ).join(DailySnapshot, Track.id == DailySnapshot.track_id).all()
        
        # Convert to list of dicts
        data = []
        for row in query:
            data.append({
                "id": row.id,
                "title": row.title,
                "artist": row.artist,
                "genre": row.genre or 'Unknown',
                "combined_emotion": row.combined_emotion,
                "lyric_emotion": row.lyric_emotion,
                "bpm": row.bpm,
                "energy": row.energy,
                "valence": row.valence,
                "spotify_viral_rank": row.spotify_viral_rank,
                "trend_weight_score": row.trend_weight_score,
                "date": row.date.isoformat()
            })
            
        # calculate high-level stats
        df = pd.DataFrame(data)
        stats = {
            "total_tracks": len(data),
            "top_vibe_today": "N/A",
            "avg_energy": 0.0
        }
        
        if not df.empty:
            top_vibe_mode = df['combined_emotion'].mode()
            stats["top_vibe_today"] = top_vibe_mode[0] if not top_vibe_mode.empty else "N/A"
            stats["avg_energy"] = round(df['energy'].mean(), 2)
            
            # Sort tracks by trend weight score for the top list
            sorted_tracks = df.sort_values(by="trend_weight_score", ascending=False).to_dict(orient="records")
        else:
            sorted_tracks = []
            
        return {
            "stats": stats,
            "tracks": sorted_tracks
        }
    except Exception as e:
        print(f"Error in dashboard endpoint: {e}")
        return {
            "stats": {"total_tracks": 0, "top_vibe_today": "Error", "avg_energy": 0.0},
            "tracks": []
        }

# Mount the static frontend AFTER all API routes
import os
if not os.path.exists("frontend"):
    os.makedirs("frontend")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
