import os
import pandas as pd
import numpy as np
from datetime import datetime
from PySide6.QtCore import QObject, Signal


LAT_PATTERNS = ["lat", "latitude", "y_coord", "ylat", "gps_lat", "latitude_dec"]
LON_PATTERNS = ["lon", "lng", "long", "longitude", "x_coord", "xlong", "gps_lon", "gps_lng", "latitude_dec"]
FIX_PATTERNS = ["fix", "quality", "fixquality", "fix_quality", "gps_quality", "fix_type", "gps_qual"]
SAT_PATTERNS = ["sat", "satellites", "satcount", "sat_count", "num_sat", "nsats", "sats", "numsats"]
TS_PATTERNS  = ["time", "timestamp", "datetime", "date_time", "ts", "gps_time", "utc", "date", "gps_utc"]

FIX_LABELS = {0: "Invalid", 1: "GPS Fix", 2: "DGPS Fix", 4: "RTK Fixed", 5: "RTK Float"}
FIX_COLORS = {0: "#ff6b6b", 1: "#ffd93d", 2: "#00d4aa", 4: "#4f9eff", 5: "#00d4aa"}

ALLOWED_EXTENSIONS = {".csv", ".txt", ".xlsx", ".xls"}


class GNSSData(QObject):
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.raw_headers = []
        self.column_map = {}
        self._raw_df = None
        self._file_path = ""

    def load_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {ext}")

        if ext in (".csv", ".txt"):
            try:
                df = pd.read_csv(filepath, encoding="utf-8", low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding="latin-1", low_memory=False)
        else:
            df = pd.read_excel(filepath, engine="openpyxl")

        df = df.dropna(how="all").reset_index(drop=True)
        df.columns = df.columns.astype(str)

        self._raw_df = df
        self._file_path = filepath
        self.raw_headers = list(df.columns)
        self.column_map = self.auto_detect_columns(self.raw_headers)
        return df

    def auto_detect_columns(self, headers):
        hl = [h.lower().strip() for h in headers]

        def find(patterns):
            for p in patterns:
                matches = [i for i, h in enumerate(hl) if p in h]
                if matches:
                    return headers[matches[0]]
            return ""

        lat = find(LAT_PATTERNS)
        lon = find(LON_PATTERNS)
        fix = find(FIX_PATTERNS)
        sat = find(SAT_PATTERNS)
        ts  = find(TS_PATTERNS)

        return {"lat": lat, "lon": lon, "fix": fix, "sat": sat, "ts": ts}

    def parse_points(self, lat_col, lon_col, fix_col="", sat_col="", ts_col=""):
        if self._raw_df is None:
            return

        df = self._raw_df.copy()
        points = []

        for idx, row in df.iterrows():
            try:
                lat = pd.to_numeric(row.get(lat_col), errors="coerce")
                lon = pd.to_numeric(row.get(lon_col), errors="coerce")
            except (ValueError, TypeError):
                continue

            if np.isnan(lat) or np.isnan(lon):
                continue
            if lat < -90 or lat > 90 or lon < -180 or lon > 180:
                continue

            fix_val = 1
            if fix_col:
                try:
                    fv = pd.to_numeric(row.get(fix_col), errors="coerce")
                    if not np.isnan(fv):
                        fix_val = int(fv)
                except (ValueError, TypeError):
                    pass

            sat_val = 0
            if sat_col:
                try:
                    sv = pd.to_numeric(row.get(sat_col), errors="coerce")
                    if not np.isnan(sv):
                        sat_val = int(sv)
                except (ValueError, TypeError):
                    pass

            ts_val = str(row.get(ts_col, "")) if ts_col else ""

            points.append({
                "lat": float(lat),
                "lon": float(lon),
                "fix": fix_val,
                "sat": min(max(sat_val, 0), 99),
                "ts": ts_val,
                "label": "",
                "estimated": fix_val == 0,
                "index": idx + 1,
            })

        self.points = points
        self.column_map = {"lat": lat_col, "lon": lon_col, "fix": fix_col, "sat": sat_col, "ts": ts_col}
        self.data_changed.emit()

    def add_manual_point(self, lat, lon, fix=1, sat=0, ts="", label=""):
        self.points.append({
            "lat": lat,
            "lon": lon,
            "fix": fix,
            "sat": min(max(sat, 0), 99),
            "ts": ts,
            "label": label,
            "estimated": fix == 0,
            "index": len(self.points) + 1,
        })
        self.data_changed.emit()

    def compute_center(self):
        valid = [p for p in self.points if p["fix"] > 0]
        src = valid if valid else self.points
        if not src:
            return None
        sum_lat = 0.0
        sum_lon = 0.0
        sum_w = 0.0
        for p in src:
            w = max(1, p["fix"] * (1 + p["sat"] * 0.1))
            sum_lat += p["lat"] * w
            sum_lon += p["lon"] * w
            sum_w += w
        return {"lat": sum_lat / sum_w, "lon": sum_lon / sum_w}

    def compute_stats(self):
        n = len(self.points)
        if not n:
            return {
                "total": 0, "valid": 0, "invalid": 0,
                "avg_sat": 0, "center": None,
                "lat_min": 0, "lat_max": 0,
                "lon_min": 0, "lon_max": 0,
                "lat_span": 0, "lon_span": 0,
            }

        valid = sum(1 for p in self.points if p["fix"] > 0)
        invalid = n - valid
        avg_sat = np.mean([p["sat"] for p in self.points])
        center = self.compute_center()

        lats = [p["lat"] for p in self.points]
        lons = [p["lon"] for p in self.points]
        lat_min, lat_max = min(lats), max(lats)
        lon_min, lon_max = min(lons), max(lons)

        return {
            "total": n,
            "valid": valid,
            "invalid": invalid,
            "avg_sat": avg_sat,
            "center": center,
            "lat_min": lat_min,
            "lat_max": lat_max,
            "lon_min": lon_min,
            "lon_max": lon_max,
            "lat_span": lat_max - lat_min,
            "lon_span": lon_max - lon_min,
        }

    def export_csv(self, filepath):
        rows = [["index", "latitude", "longitude", "fix_quality", "satellite_count", "timestamp", "label"]]
        for p in self.points:
            rows.append([p["index"], p["lat"], p["lon"], p["fix"], p["sat"], p["ts"], p["label"]])
        df = pd.DataFrame(rows[1:], columns=rows[0])
        df.to_csv(filepath, index=False)

    def clear(self):
        self.points = []
        self._raw_df = None
        self._file_path = ""
        self.raw_headers = []
        self.column_map = {}
        self.data_changed.emit()
