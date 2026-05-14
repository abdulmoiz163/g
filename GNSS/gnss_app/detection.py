import math
import numpy as np


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def detect_anomalies(points, speed_thresh=100.0, outlier_std=3.0, min_sats=4):
    results = []

    if len(points) < 2:
        if len(points) == 0:
            return results
        results.append({
            "type": "info",
            "title": "Insufficient Data",
            "desc": "Need at least 2 points for detection. Only 1 point loaded.",
            "icon": "info",
            "point_index": points[0]["index"],
        })
        return results

    # 1. Speed-based anomaly detection
    for i in range(1, len(points)):
        p0, p1 = points[i - 1], points[i]
        dist = haversine(p0["lat"], p0["lon"], p1["lat"], p1["lon"])

        ts0, ts1 = p0.get("ts", ""), p1.get("ts", "")
        speed_ms = None
        if ts0 and ts1:
            try:
                import pandas as pd
                t0 = pd.to_datetime(ts0)
                t1 = pd.to_datetime(ts1)
                dt = (t1 - t0).total_seconds()
                if dt > 0:
                    speed_ms = dist / dt
            except Exception:
                pass

        if speed_ms is not None and speed_ms > speed_thresh:
            results.append({
                "type": "anomaly",
                "title": f"High Speed: {speed_ms:.1f} m/s",
                "desc": f"Between point #{p0['index']} and #{p1['index']}. "
                        f"Distance: {dist:.0f}m | Speed threshold: {speed_thresh} m/s",
                "icon": "fa-gauge-high",
                "point_index": p1["index"],
                "severity": min(speed_ms / speed_thresh, 10),
                "lat": p1["lat"],
                "lon": p1["lon"],
            })

    # 2. Fix quality drop detection
    for i in range(1, len(points)):
        p0, p1 = points[i - 1], points[i]
        if p0["fix"] > 1 and p1["fix"] == 0:
            results.append({
                "type": "warning",
                "title": "Fix Quality Drop",
                "desc": f"Point #{p1['index']}: Fix dropped from {p0['fix']} to 0 (Invalid). "
                        f"Satellites: {p1.get('sat', '?')}",
                "icon": "fa-signal",
                "point_index": p1["index"],
                "severity": 3.0,
                "lat": p1["lat"],
                "lon": p1["lon"],
            })

    # 3. Low satellite count
    for p in points:
        if 0 < p.get("sat", 0) < min_sats:
            results.append({
                "type": "warning",
                "title": f"Low Satellites: {p['sat']}",
                "desc": f"Point #{p['index']}: Only {p['sat']} satellites (recommended: {min_sats}+). "
                        f"Fix quality: {p['fix']}",
                "icon": "fa-satellite",
                "point_index": p["index"],
                "severity": 2.0,
                "lat": p["lat"],
                "lon": p["lon"],
            })

    # 4. Position outliers (using IQR / z-score on distance from centroid)
    if len(points) >= 3:
        center_lat = np.mean([p["lat"] for p in points])
        center_lon = np.mean([p["lon"] for p in points])

        distances = []
        for p in points:
            d = haversine(center_lat, center_lon, p["lat"], p["lon"])
            distances.append(d)

        mean_d = np.mean(distances)
        std_d = np.std(distances)

        if std_d > 0:
            for i, p in enumerate(points):
                z = (distances[i] - mean_d) / std_d
                if abs(z) > outlier_std:
                    results.append({
                        "type": "anomaly" if abs(z) > outlier_std * 1.5 else "warning",
                        "title": f"Position Outlier (z={z:.1f})",
                        "desc": f"Point #{p['index']}: {distances[i]:.0f}m from centroid "
                                f"(threshold: {outlier_std} std devs)",
                        "icon": "fa-location-dot",
                        "point_index": p["index"],
                        "severity": min(abs(z) / outlier_std, 10),
                        "lat": p["lat"],
                        "lon": p["lon"],
                    })

    # 5. Cluster info - find dense clusters
    if len(points) >= 5:
        cluster_threshold = 50
        clusters = []
        assigned = set()
        for i in range(len(points)):
            if i in assigned:
                continue
            cluster = [i]
            assigned.add(i)
            for j in range(i + 1, len(points)):
                if j in assigned:
                    continue
                d = haversine(points[i]["lat"], points[i]["lon"],
                              points[j]["lat"], points[j]["lon"])
                if d < cluster_threshold:
                    cluster.append(j)
                    assigned.add(j)
            if len(cluster) >= 3:
                clusters.append(cluster)

        if clusters:
            total_clustered = sum(len(c) for c in clusters)
            results.append({
                "type": "cluster",
                "title": f"{len(clusters)} Dense Clusters Found",
                "desc": f"{total_clustered} points within {cluster_threshold}m of each other "
                        f"({total_clustered / len(points) * 100:.0f}% of data)",
                "icon": "fa-layer-group",
                "point_index": None,
                "severity": 0,
                "lat": None,
                "lon": None,
            })

    if not results:
        results.append({
            "type": "info",
            "title": "No Anomalies Detected",
            "desc": f"All {len(points)} points passed checks.",
            "icon": "fa-check-circle",
            "point_index": None,
            "severity": 0,
            "lat": None,
            "lon": None,
        })

    results.sort(key=lambda r: (
        {"anomaly": 0, "warning": 1, "cluster": 2, "info": 3}.get(r["type"], 4),
        -r.get("severity", 0)
    ))
    return results
