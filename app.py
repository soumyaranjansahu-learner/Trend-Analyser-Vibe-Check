import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Track, DailySnapshot

# Configure page
st.set_page_config(page_title="VIBE-CHECK Dashboard", page_icon="🎵", layout="wide")

# Custom CSS for aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #121212;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1DB954;
    }
    .metric-label {
        font-size: 1.2rem;
        color: #A0A0A0;
    }
    h1, h2, h3 {
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    db = SessionLocal()
    return db

def load_data(db: Session):
    # Load all tracks with their latest snapshot
    query = db.query(
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
    
    return pd.DataFrame(query)

db = get_db()
df = load_data(db)

st.title("🎧 VIBE-CHECK Dashboard")
st.markdown("Real-time tracking of music trends categorized by **Emotion** and **Genre**.")

if df.empty:
    st.warning("No data found in the database. Please run `data_pipeline.py` to ingest data.")
else:
    # Filter Controls
    st.sidebar.header("🎯 Vibe Filter")
    
    # Extract unique emotions and genres
    emotions = sorted(list(df['combined_emotion'].dropna().unique()))
    genres = sorted(list(df['genre'].fillna('Unknown').unique()))
    
    selected_emotion = st.sidebar.selectbox("Select Emotion Vibe", ["All"] + emotions)
    selected_genre = st.sidebar.selectbox("Select Genre", ["All"] + genres)
    
    # Apply Filters
    filtered_df = df.copy()
    if selected_emotion != "All":
        filtered_df = filtered_df[filtered_df['combined_emotion'] == selected_emotion]
    if selected_genre != "All":
        # Handle 'Unknown' mapping
        filtered_df = filtered_df[filtered_df['genre'].fillna('Unknown') == selected_genre]
        
    # Top KPI Metrics using columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-label'>Trending Tracks Tracking</div><div class='metric-value'>{len(df)}</div>", unsafe_allow_html=True)
    with col2:
        top_vibe = df['combined_emotion'].mode()[0] if not df.empty else "N/A"
        st.markdown(f"<div class='metric-label'>Global Top Vibe Today</div><div class='metric-value'>{top_vibe}</div>", unsafe_allow_html=True)
    with col3:
        avg_rpm = df['bpm'].mean()
        st.markdown(f"<div class='metric-label'>Global Average Energy</div><div class='metric-value'>{df['energy'].mean():.2f}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Main Visualizations
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Daily Vibe Shift (Valence vs Energy)")
        # Plotly scatter for Circumplex mapping
        if not filtered_df.empty:
            fig1 = px.scatter(
                filtered_df, 
                x="valence", 
                y="energy", 
                color="combined_emotion",
                hover_data=["title", "artist"],
                title="Arousal vs Valence of Trending Music",
                template="plotly_dark"
            )
            fig1.update_traces(marker=dict(size=12, opacity=0.8))
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No data available for these filters.")
            
    with col_chart2:
        st.subheader("Top Correlated Lyrics Emotion")
        if not filtered_df.empty:
            lyric_counts = filtered_df['lyric_emotion'].value_counts().reset_index()
            lyric_counts.columns = ['Emotion', 'Count']
            fig2 = px.bar(
                lyric_counts, 
                x="Emotion", 
                y="Count", 
                color="Emotion",
                title="Lyric Sentiment Distribution",
                template="plotly_dark"
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📊 Top Trending Tracks Context")
    display_df = filtered_df[['title', 'artist', 'combined_emotion', 'genre', 'spotify_viral_rank', 'trend_weight_score']]
    st.dataframe(display_df.sort_values(by="trend_weight_score", ascending=False).head(20), use_container_width=True)

