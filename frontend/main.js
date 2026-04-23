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
        const response = await fetch("/api/dashboard");
        if (!response.ok) throw new Error("Failed to fetch API");
        const data = await response.json();
        
        globalData = data;
        
        populateFilters(data.tracks);
        renderDashboard(data.tracks);
        updateKPIs(data.stats);

    } catch (e) {
        console.error("Error loading dashboard:", e);
        document.getElementById("kpi-vibe").innerHTML = "<span style='color: #fe0979; font-size: 1.5rem;'>Error Loading</span>";
        document.getElementById("kpi-total").innerText = "0";
        document.getElementById("kpi-energy").innerText = "0.0";
        document.getElementById("tracks-body").innerHTML = "<tr><td colspan='5'>Error fetching tracks.</td></tr>";
    }
}

function populateFilters(tracks) {
    const emotionFilter = document.getElementById("emotion-filter");
    const genreFilter = document.getElementById("genre-filter");
    
    // Reset options
    emotionFilter.innerHTML = '<option value="All">All Emotions</option>';
    genreFilter.innerHTML = '<option value="All">All Genres</option>';

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
    
    // Update total count smoothly
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
    
    if (tracks.length === 0) {
        tbody.innerHTML = "<tr><td colspan='5' style='text-align:center; padding: 2rem; color: #8e8e9f;'>Fetching latest trend data... Give it a few seconds and refresh.</td></tr>";
        return;
    }

    const topTracks = tracks.slice(0, 20);
    
    topTracks.forEach((t, i) => {
        const tr = document.createElement("tr");
        
        tr.innerHTML = `
            <td>#${i + 1}</td>
            <td>
                <strong style="color: #fff; font-size: 1.05rem;">${t.title}</strong><br>
                <span style="font-size: 0.85rem; color: #8e8e9f">${t.artist}</span>
            </td>
            <td><span class="vibe-tag">${t.combined_emotion || 'Unknown'}</span></td>
            <td>${t.genre}</td>
            <td style="color: #00f2fe;">${parseFloat(t.trend_weight_score || 0).toFixed(2)}</td>
        `;
        
        tbody.appendChild(tr);
    });
}

function renderChart(tracks) {
    const ctx = document.getElementById('vibeChart').getContext('2d');
    
    const datasetMap = {};
    const colors = ['#00f2fe', '#fe0979', '#1DB954', '#f5af19', '#e0c3fc', '#4facfe'];
    
    tracks.forEach(t => {
        const vibe = t.combined_emotion || 'Neutral';
        if(!datasetMap[vibe]) {
            datasetMap[vibe] = {
                label: vibe,
                data: [],
                backgroundColor: colors[Object.keys(datasetMap).length % colors.length],
                borderColor: 'rgba(255,255,255,0.8)',
                borderWidth: 1,
                pointRadius: 8,
                pointHoverRadius: 12,
                pointHoverBackgroundColor: '#ffffff'
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
            color: '#9aa0a6',
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: { color: '#ffffff', font: { family: 'Outfit', size: 12 }, usePointStyle: true, boxWidth: 8 }
                },
                tooltip: {
                    backgroundColor: 'rgba(5, 5, 10, 0.9)',
                    titleColor: '#00f2fe',
                    bodyColor: '#ffffff',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(ctx) {
                            const p = ctx.raw;
                            return [
                                `${p.title}`,
                                `By: ${p.artist}`,
                                `Energy: ${p.y.toFixed(2)} | Valence: ${p.x.toFixed(2)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Valence (Sad → Happy)', color: '#9aa0a6', font: { family: 'Outfit' } },
                    grid: { color: 'rgba(255,255,255,0.02)' },
                    ticks: { color: '#9aa0a6' },
                    min: 0,
                    max: 1
                },
                y: {
                    title: { display: true, text: 'Energy (Calm → Intense)', color: '#9aa0a6', font: { family: 'Outfit' } },
                    grid: { color: 'rgba(255,255,255,0.02)' },
                    ticks: { color: '#9aa0a6' },
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
