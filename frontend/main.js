let globalData = {
    stats: {},
    tracks: []
};
let vibeChartInstance = null;

// Initialize when DOM loaded
document.addEventListener("DOMContentLoaded", () => {
    fetchData();

    document.getElementById("apply-filters").addEventListener("click", () => {
        applyFilters();
    });
});

async function fetchData() {
    try {
        // Fetch from API Server relative path
        const response = await fetch("/api/dashboard");
        if (!response.ok) throw new Error("Failed to fetch API");
        const data = await response.json();
        
        globalData = data;
        
        // Populate options
        populateFilters(data.tracks);
        
        // Initial Render
        renderDashboard(data.tracks);
        updateKPIs(data.stats);

    } catch (e) {
        console.error("Error loading dashboard:", e);
        document.getElementById("kpi-vibe").innerText = "Error Loading";
    }
}

function populateFilters(tracks) {
    const emotionFilter = document.getElementById("emotion-filter");
    const genreFilter = document.getElementById("genre-filter");
    
    const emotions = new Set();
    const genres = new Set();
    
    tracks.forEach(t => {
        if(t.combined_emotion) emotions.add(t.combined_emotion);
        if(t.genre) genres.add(t.genre);
    });
    
    emotions.forEach(e => {
        const opt = document.createElement("option");
        opt.value = e;
        opt.innerText = e;
        emotionFilter.appendChild(opt);
    });
    
    genres.forEach(g => {
        const opt = document.createElement("option");
        opt.value = g;
        opt.innerText = g;
        genreFilter.appendChild(opt);
    });
}

function applyFilters() {
    const e_val = document.getElementById("emotion-filter").value;
    const g_val = document.getElementById("genre-filter").value;
    
    let filtered = globalData.tracks;
    
    if(e_val !== "All") {
        filtered = filtered.filter(t => t.combined_emotion === e_val);
    }
    if(g_val !== "All") {
        filtered = filtered.filter(t => t.genre === g_val);
    }
    
    renderDashboard(filtered);
    
    // Update total count
    document.getElementById("kpi-total").innerText = filtered.length;
}

function updateKPIs(stats) {
    document.getElementById("kpi-total").innerText = stats.total_tracks;
    document.getElementById("kpi-vibe").innerText = stats.top_vibe_today;
    document.getElementById("kpi-energy").innerText = stats.avg_energy;
}

function renderDashboard(tracks) {
    renderTable(tracks);
    renderChart(tracks);
}

function renderTable(tracks) {
    const tbody = document.getElementById("tracks-body");
    tbody.innerHTML = "";
    
    // Render top 20
    const topTracks = tracks.slice(0, 20);
    
    topTracks.forEach((t, i) => {
        const tr = document.createElement("tr");
        
        tr.innerHTML = `
            <td>#${i + 1}</td>
            <td>
                <strong style="color: #fff">${t.title}</strong><br>
                <span style="font-size: 0.8rem; color: #8e8e9f">${t.artist}</span>
            </td>
            <td><span class="vibe-tag">${t.combined_emotion || 'Unknown'}</span></td>
            <td>${t.genre}</td>
            <td>${parseFloat(t.trend_weight_score || 0).toFixed(2)}</td>
        `;
        
        tbody.appendChild(tr);
    });
}

function renderChart(tracks) {
    const ctx = document.getElementById('vibeChart').getContext('2d');
    
    // Prepare data for Chart.js scatter plot
    // Grouping by combined_emotion for different colors
    const datasetMap = {};
    
    // Simple color palette generator
    const colors = ['#00f2fe', '#4facfe', '#1DB954', '#f12711', '#f5af19', '#e0c3fc'];
    
    tracks.forEach(t => {
        const vibe = t.combined_emotion || 'Neutral';
        if(!datasetMap[vibe]) {
            datasetMap[vibe] = {
                label: vibe,
                data: [],
                backgroundColor: colors[Object.keys(datasetMap).length % colors.length],
                pointRadius: 6,
                pointHoverRadius: 9
            };
        }
        datasetMap[vibe].data.push({
            x: t.valence || 0.5,
            y: t.energy || 0.5,
            title: t.title,
            artist: t.artist
        });
    });

    const config = {
        type: 'scatter',
        data: {
            datasets: Object.values(datasetMap)
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            color: '#8e8e9f',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#ffffff', font: { family: 'Outfit' } }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const p = ctx.raw;
                            return `${p.title} - ${p.artist}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Valence (Negative to Positive)', color: '#8e8e9f' },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#8e8e9f' },
                    min: 0,
                    max: 1
                },
                y: {
                    title: { display: true, text: 'Energy (Low to High)', color: '#8e8e9f' },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#8e8e9f' },
                    min: 0,
                    max: 1
                }
            }
        }
    };

    if (vibeChartInstance) {
        vibeChartInstance.destroy();
    }
    vibeChartInstance = new Chart(ctx, config);
}
