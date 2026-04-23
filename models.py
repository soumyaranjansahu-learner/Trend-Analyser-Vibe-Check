import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Track(Base):
    """
    Represents a unique song.
    """
    __tablename__ = "tracks"

    id = Column(String, primary_key=True, index=True) # Spotify Track ID
    title = Column(String, index=True)
    artist = Column(String, index=True)
    genre = Column(String, nullable=True) # E.g., 'pop', 'hip hop'
    
    # Audio Features (from Spotipy / Librosa)
    bpm = Column(Float, nullable=True)
    energy = Column(Float, nullable=True)
    key = Column(Integer, nullable=True)
    valence = Column(Float, nullable=True) # High = positive, Low = negative
    
    # Text Features (from Lyrics)
    lyrics = Column(String, nullable=True)
    lyric_emotion = Column(String, nullable=True) # 'Joy', 'Sadness', 'Anger', 'Fear', 'Surprise', 'Love'
    
    # Combined multi-modal emotion
    combined_emotion = Column(String, nullable=True) 

    # Relationships
    snapshots = relationship("DailySnapshot", back_populates="track", cascade="all, delete-orphan")

class DailySnapshot(Base):
    """
    Daily rank snapshot to calculate Trend-Weight Algorithm
    """
    __tablename__ = "daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String, ForeignKey("tracks.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Source specific rankings
    spotify_viral_rank = Column(Integer, nullable=True)
    billboard_hot_100_rank = Column(Integer, nullable=True)
    
    # Calculated scores
    social_velocity = Column(Float, default=0.0)
    trend_weight_score = Column(Float, default=0.0)

    track = relationship("Track", back_populates="snapshots")
