import json
import os


_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

with open(os.path.join(_RESOURCES_DIR, "leaflet.min.css"), "r", encoding="utf-8") as f:
    _LEAFLET_CSS = f.read()

with open(os.path.join(_RESOURCES_DIR, "leaflet.min.js"), "r", encoding="utf-8") as f:
    _LEAFLET_JS = f.read()


def generate_map_html(points):
    points_json = json.dumps([
        {
            "lat": p["lat"],
            "lon": p["lon"],
            "fix": p["fix"],
            "sat": p["sat"],
            "ts": str(p.get("ts", "")),
            "label": str(p.get("label", "")),
            "estimated": p.get("estimated", False),
            "index": p.get("index", 0),
        }
        for p in points
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GNSS Map</title>
<style>
{_LEAFLET_CSS}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0d15; overflow: hidden; }}
#map {{ width: 100vw; height: 100vh; }}
.leaflet-tile-pane {{ filter: brightness(0.6) hue-rotate(15deg) saturate(0.8); }}
.leaflet-popup-content-wrapper {{ background: #141720; border: 1px solid #2a3050; color: #e8ecf5; border-radius: 10px; font-family: 'Segoe UI', sans-serif; }}
.leaflet-popup-tip {{ background: #141720; }}
.leaflet-popup-content {{ margin: 10px 12px; }}
.leaflet-control-zoom a {{ background: #1c2030; color: #9aa3bf; border-color: #2a3050; }}
.leaflet-control-zoom a:hover {{ background: #252a3a; color: #4f9eff; }}

.map-legend {{
  position: absolute; bottom: 20px; left: 20px;
  background: rgba(20,23,32,0.92); border: 1px solid #3a4570;
  border-radius: 10px; padding: 12px 14px; z-index: 1000;
  font-size: 11px; backdrop-filter: blur(8px);
  font-family: 'Segoe UI', sans-serif; min-width: 150px;
}}
.legend-title {{ color: #5a6480; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; font-size: 10px; margin-bottom: 8px; }}
.legend-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; color: #9aa3bf; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}

.coord-display {{
  position: absolute; bottom: 20px; right: 20px;
  background: rgba(20,23,32,0.92); border: 1px solid #3a4570;
  border-radius: 10px; padding: 8px 12px; z-index: 1000;
  font-size: 11px; font-family: 'Consolas', monospace; color: #9aa3bf;
  backdrop-filter: blur(8px);
}}

.map-controls {{
  position: absolute; top: 16px; right: 16px; z-index: 1000;
  display: flex; flex-direction: column; gap: 6px;
}}
.map-btn {{
  width: 36px; height: 36px; background: #141720; border: 1px solid #3a4570;
  border-radius: 8px; color: #9aa3bf; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; transition: all 0.15s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}}
.map-btn:hover {{ background: #252a3a; color: #4f9eff; border-color: #4f9eff; }}

.est-badge {{
  position: absolute; top: 16px; left: 50%; transform: translateX(-50%);
  background: rgba(255,217,61,0.12); border: 1px solid rgba(255,217,61,0.4);
  border-radius: 20px; padding: 5px 14px; font-size: 12px;
  color: #ffd93d; z-index: 1000; display: none;
  white-space: nowrap; backdrop-filter: blur(8px);
  font-family: 'Segoe UI', sans-serif;
}}
.est-badge.visible {{ display: block; }}

.popup-row {{ display: flex; justify-content: space-between; padding: 2px 0; font-size: 11px; }}
.popup-key {{ color: #5a6480; }}
.popup-val {{ color: #e8ecf5; font-weight: 500; }}
</style>
</head>
<body>
<div id="map"></div>

<div class="est-badge" id="estBadge">
  <span>&#9888;</span> Contains estimated / low-quality fixes
</div>

<div class="map-controls">
  <button class="map-btn" onclick="fitBounds()" title="Fit all points">&#8690;</button>
  <button class="map-btn" onclick="toggleSize()" title="Toggle marker sizing">&#9733;</button>
</div>

<div class="map-legend">
  <div class="legend-title">Fix Quality</div>
  <div class="legend-item"><div class="legend-dot" style="background:#4f9eff"></div>RTK Fixed (4)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#00d4aa"></div>DGPS / RTK Float</div>
  <div class="legend-item"><div class="legend-dot" style="background:#ffd93d"></div>GPS Fix (1)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#ff6b6b"></div>Invalid (0)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#b06dff;border:2px solid #b06dff;"></div>Estimated</div>
</div>

<div class="coord-display" id="coordDisplay">&#10010; Hover map for coordinates</div>

<script>
{_LEAFLET_JS}
</script>
<script>
const DATA = {points_json};

const FIX_COLORS = {{0: "#ff6b6b", 1: "#ffd93d", 2: "#00d4aa", 4: "#4f9eff", 5: "#00d4aa"}};
const FIX_LABELS = {{0: "Invalid", 1: "GPS Fix", 2: "DGPS Fix", 4: "RTK Fixed", 5: "RTK Float"}};

const map = L.map('map', {{
  center: [24.8607, 67.0011],
  zoom: 5,
  zoomControl: false,
}});

L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '&copy; OpenStreetMap'
}}).addTo(map);

L.control.zoom({{ position: 'topright' }}).addTo(map);

let markers = [];
let sizeSized = true;

function getColor(fix, estimated) {{
  if (estimated) return '#b06dff';
  return FIX_COLORS[fix] || '#ffd93d';
}}

function getSize(sat) {{
  return Math.max(8, Math.min(18, 8 + (sat || 0) * 0.5));
}}

function addMarkers(pts) {{
  pts.forEach(p => {{
    const color = getColor(p.fix, p.estimated);
    const size = getSize(p.sat);

    const icon = L.divIcon({{
      className: '',
      html: `<div style="
        width:${{size}}px; height:${{size}}px;
        background:${{color}};
        border-radius:50%;
        border:2px solid rgba(255,255,255,0.4);
        box-shadow: 0 0 6px ${{color}}88, 0 2px 4px rgba(0,0,0,0.5);
        cursor:pointer;
      "></div>`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
    }});

    const m = L.marker([p.lat, p.lon], {{ icon }}).addTo(map);

    m.bindPopup(`
      <div class="popup-row"><span class="popup-key">Point</span><span class="popup-val">#${{p.index}}</span></div>
      <div class="popup-row"><span class="popup-key">Latitude</span><span class="popup-val">${{p.lat.toFixed(7)}}</span></div>
      <div class="popup-row"><span class="popup-key">Longitude</span><span class="popup-val">${{p.lon.toFixed(7)}}</span></div>
      <div class="popup-row"><span class="popup-key">Fix Quality</span><span class="popup-val">${{p.fix}} — ${{FIX_LABELS[p.fix] || 'Unknown'}}</span></div>
      <div class="popup-row"><span class="popup-key">Satellites</span><span class="popup-val">${{p.sat || '—'}}</span></div>
      <div class="popup-row"><span class="popup-key">Timestamp</span><span class="popup-val">${{(p.ts || '—').substring(0, 19)}}</span></div>
      ${{p.label ? `<div class="popup-row"><span class="popup-key">Label</span><span class="popup-val">${{p.label}}</span></div>` : ''}}
      ${{p.estimated ? '<div style="margin-top:6px;padding:4px 6px;background:rgba(176,109,255,0.1);border:1px solid rgba(176,109,255,0.3);border-radius:4px;font-size:10px;color:#b06dff;">&#9888; Estimated position</div>' : ''}}
    `);

    markers.push(m);
  }});
}}

function fitBounds() {{
  if (!DATA.length) return;
  const lats = DATA.map(p => p.lat);
  const lons = DATA.map(p => p.lon);
  map.fitBounds([
    [Math.min(...lats), Math.min(...lons)],
    [Math.max(...lats), Math.max(...lons)]
  ], {{ padding: [40, 40] }});
}}

function toggleSize() {{
  sizeSized = !sizeSized;
  markers.forEach((m, i) => {{
    const p = DATA[i];
    const s = sizeSized ? getSize(p.sat) : 11;
    const color = getColor(p.fix, p.estimated);
    m.setIcon(L.divIcon({{
      className: '',
      html: `<div style="width:${{s}}px;height:${{s}}px;background:${{color}};border-radius:50%;border:2px solid rgba(255,255,255,0.4);box-shadow:0 0 6px ${{color}}88,0 2px 4px rgba(0,0,0,0.5);cursor:pointer;"></div>`,
      iconSize: [s, s],
      iconAnchor: [s / 2, s / 2],
    }}));
  }});
}}

map.on('mousemove', e => {{
  document.getElementById('coordDisplay').innerHTML =
    `&#10010; ${{e.latlng.lat.toFixed(6)}}, ${{e.latlng.lng.toFixed(6)}}`;
}});

addMarkers(DATA);

if (DATA.length) {{
  fitBounds();
}}

const hasEst = DATA.some(p => p.estimated);
if (hasEst) document.getElementById('estBadge').classList.add('visible');
</script>
</body>
</html>"""
    return html
