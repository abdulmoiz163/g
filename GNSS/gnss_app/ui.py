import os
import sys
import tempfile

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QFileDialog, QListWidget, QListWidgetItem, QFrame, QSplitter,
    QHeaderView, QAbstractItemView, QMessageBox, QLineEdit,
    QSpinBox, QDoubleSpinBox, QDateTimeEdit, QScrollArea,
    QCheckBox, QGridLayout, QGroupBox, QFormLayout, QSizePolicy,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QPalette, QAction, QDragEnterEvent, QDropEvent
import pandas as pd

from data_model import GNSSData, FIX_LABELS, ALLOWED_EXTENSIONS
from map_template import generate_map_html
from detection import detect_anomalies

DARK_BG = "#0d0f14"
DARK_SURFACE = "#141720"
DARK_SURFACE2 = "#1c2030"
DARK_SURFACE3 = "#252a3a"
DARK_BORDER = "#2a3050"
DARK_BORDER2 = "#3a4570"
DARK_ACCENT = "#4f9eff"
DARK_ACCENT2 = "#00d4aa"
DARK_ACCENT3 = "#ff6b6b"
DARK_ACCENT4 = "#ffd93d"
DARK_TEXT = "#e8ecf5"
DARK_TEXT2 = "#9aa3bf"
DARK_TEXT3 = "#5a6480"

STYLESHEET = f"""
QMainWindow {{ background-color: {DARK_BG}; }}
QWidget {{ background-color: {DARK_BG}; color: {DARK_TEXT}; font-family: 'Segoe UI', 'Arial', sans-serif; }}
QLabel {{ color: {DARK_TEXT}; background: transparent; }}
QPushButton {{
    background-color: {DARK_SURFACE3}; color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER2}; border-radius: 6px;
    padding: 6px 14px; font-size: 12px; font-weight: 500;
}}
QPushButton:hover {{ background-color: {DARK_SURFACE2}; border-color: {DARK_ACCENT}; }}
QPushButton:pressed {{ background-color: {DARK_SURFACE3}; }}
QPushButton:disabled {{ opacity: 0.4; color: {DARK_TEXT3}; }}
QComboBox {{
    background-color: {DARK_SURFACE2}; color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER}; border-radius: 5px;
    padding: 4px 8px; font-size: 12px; min-height: 20px;
}}
QComboBox:hover {{ border-color: {DARK_ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox::down-arrow {{ image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid {DARK_TEXT2}; margin-right: 6px; }}
QComboBox QAbstractItemView {{
    background-color: {DARK_SURFACE2}; color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER2}; selection-background-color: {DARK_SURFACE3};
    outline: none;
}}
QLineEdit, QSpinBox, QDoubleSpinBox, QDateTimeEdit {{
    background-color: {DARK_SURFACE2}; color: {DARK_TEXT};
    border: 1px solid {DARK_BORDER}; border-radius: 5px;
    padding: 5px 8px; font-size: 12px; font-family: 'Consolas', 'Courier New', monospace;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus {{
    border-color: {DARK_ACCENT};
}}
QTableWidget {{
    background-color: {DARK_SURFACE}; color: {DARK_TEXT2};
    border: 1px solid {DARK_BORDER}; font-size: 11px;
    font-family: 'Consolas', 'Courier New', monospace;
    gridline-color: rgba(42,48,80,0.5);
}}
QTableWidget::item {{ padding: 4px 8px; }}
QTableWidget::item:selected {{ background-color: rgba(79,158,255,0.15); color: {DARK_TEXT}; }}
QHeaderView::section {{
    background-color: {DARK_SURFACE3}; color: {DARK_TEXT3};
    padding: 6px 8px; border: none; border-bottom: 1px solid {DARK_BORDER};
    font-weight: 500; font-size: 11px;
}}
QScrollBar:vertical {{
    width: 6px; background: {DARK_SURFACE};
}}
QScrollBar::handle:vertical {{
    background: {DARK_BORDER2}; border-radius: 3px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {DARK_TEXT3}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    height: 6px; background: {DARK_SURFACE};
}}
QScrollBar::handle:horizontal {{
    background: {DARK_BORDER2}; border-radius: 3px; min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {DARK_TEXT3}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QTabWidget::pane {{
    border: none; background: transparent;
}}
QTabBar::tab {{
    background: transparent; color: {DARK_TEXT3}; padding: 10px 14px;
    border-bottom: 2px solid transparent; font-size: 12px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.3px;
}}
QTabBar::tab:selected {{
    color: {DARK_ACCENT}; border-bottom-color: {DARK_ACCENT};
    background: rgba(79,158,255,0.05);
}}
QTabBar::tab:hover {{ color: {DARK_TEXT2}; }}
QListWidget {{
    background-color: {DARK_SURFACE}; color: {DARK_TEXT2};
    border: 1px solid {DARK_BORDER}; border-radius: 6px;
    font-size: 12px;
}}
QListWidget::item {{ padding: 6px 8px; }}
QListWidget::item:selected {{ background: rgba(79,158,255,0.1); color: {DARK_TEXT}; }}
QCheckBox {{
    spacing: 6px; color: {DARK_TEXT2}; font-size: 12px;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {DARK_BORDER2};
    border-radius: 3px; background: {DARK_SURFACE2};
}}
QCheckBox::indicator:checked {{
    background: {DARK_ACCENT}; border-color: {DARK_ACCENT};
}}
QGroupBox {{
    border: 1px solid {DARK_BORDER}; border-radius: 8px;
    margin-top: 12px; padding-top: 16px; font-weight: 500;
    color: {DARK_TEXT2};
}}
QGroupBox::title {{
    subcontrol-origin: margin; padding: 0 8px; color: {DARK_TEXT3};
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
}}
QFrame {{ border: none; }}
QSplitter::handle {{ background: {DARK_BORDER}; width: 1px; }}
"""


class DropZone(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(160)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_SURFACE2};
                border: 2px dashed {DARK_BORDER2};
                border-radius: 12px;
            }}
            QWidget:hover {{
                border-color: {DARK_ACCENT};
                background-color: rgba(79,158,255,0.06);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel("\U0001F4C2")
        self.icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        title = QLabel("Drop file here or click to browse")
        title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DARK_TEXT}; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Supports CSV, TXT, XLSX, XLS \u2014 auto-detects column mapping")
        sub.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT3}; background: transparent;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        tags_w = QHBoxLayout()
        tags_w.setAlignment(Qt.AlignCenter)
        for tag, color in [("CSV", DARK_ACCENT), ("XLSX", DARK_ACCENT2), ("TXT", DARK_ACCENT4)]:
            lbl = QLabel(tag)
            lbl.setStyleSheet(f"""
                background: rgba({','.join(str(int(c,16)) for c in (color[1:3], color[3:5], color[5:7]) )}, 0.15);
                color: {color}; border: 1px solid rgba({','.join(str(int(c,16)) for c in (color[1:3], color[3:5], color[5:7]) )}, 0.3);
                border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 500;
            """)
            tags_w.addWidget(lbl)
        layout.addLayout(tags_w)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: rgba(79,158,255,0.08);
                    border: 2px dashed {DARK_ACCENT};
                    border-radius: 12px;
                }}
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_SURFACE2};
                border: 2px dashed {DARK_BORDER2};
                border-radius: 12px;
            }}
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DARK_SURFACE2};
                border: 2px dashed {DARK_BORDER2};
                border-radius: 12px;
            }}
        """)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            parent = self.parent()
            while parent and not hasattr(parent, 'load_file'):
                parent = parent.parent()
            if parent and hasattr(parent, 'load_file'):
                parent.load_file(path)

    def mousePressEvent(self, event):
        parent = self.parent()
        while parent and not hasattr(parent, 'browse_file'):
            parent = parent.parent()
        if parent and hasattr(parent, 'browse_file'):
            parent.browse_file()


class StatsCard(QFrame):
    def __init__(self, label, value="\u2014", sub="", color=None):
        super().__init__()
        self.setStyleSheet(f"background-color: {DARK_SURFACE}; border-right: 1px solid {DARK_BORDER};")
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 10px; color: {DARK_TEXT3}; letter-spacing: 0.5px; text-transform: uppercase; font-weight: 500; background: transparent;")
        layout.addWidget(lbl)

        self.val_label = QLabel(value)
        val_style = f"font-size: 20px; font-weight: 700; font-family: 'Consolas', monospace; color: {DARK_TEXT}; background: transparent;"
        if color:
            val_style += f" color: {color};"
        self.val_label.setStyleSheet(val_style)
        layout.addWidget(self.val_label)

        self.sub_label = QLabel(sub)
        self.sub_label.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT3}; font-family: 'Consolas', monospace; background: transparent;")
        layout.addWidget(self.sub_label)

    def set_value(self, value, color=None):
        self.val_label.setText(value)
        if color:
            self.val_label.setStyleSheet(
                f"font-size: 20px; font-weight: 700; font-family: 'Consolas', monospace; color: {color}; background: transparent;"
            )

    def set_sub(self, text):
        self.sub_label.setText(text)


class MapWidget(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0a0d15; border: none;")
        self.map_html = ""

    def update_map(self, points):
        self.map_html = generate_map_html(points)
        self.setHtml(self.map_html)


class ImportTab(QWidget):
    def __init__(self, data_model: GNSSData, main_window):
        super().__init__()
        self.data_model = data_model
        self.main_window = main_window
        self.data_model.data_changed.connect(self.on_data_changed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.drop_zone = DropZone(self)
        layout.addWidget(self.drop_zone, 0, Qt.AlignTop)

        section = QLabel("  Column Mapping")
        section.setStyleSheet(f"padding: 10px 14px; font-size: 11px; font-weight: 600; color: {DARK_TEXT3}; letter-spacing: 0.8px; text-transform: uppercase; border-bottom: 1px solid {DARK_BORDER};")
        layout.addWidget(section)

        grid = QGridLayout()
        grid.setContentsMargins(14, 10, 14, 10)
        grid.setSpacing(8)

        def make_combo():
            c = QComboBox()
            c.addItem("\u2014 Select \u2014", "")
            c.setMinimumWidth(120)
            return c

        self.cb_lat = make_combo()
        self.cb_lon = make_combo()
        self.cb_fix = make_combo()
        self.cb_sat = make_combo()
        self.cb_ts = make_combo()

        grid.addWidget(QLabel("\u25CF Latitude"), 0, 0)
        grid.addWidget(self.cb_lat, 0, 1)
        grid.addWidget(QLabel("\u25CF Longitude"), 1, 0)
        grid.addWidget(self.cb_lon, 1, 1)
        grid.addWidget(QLabel("\u25A0 Fix Quality"), 2, 0)
        grid.addWidget(self.cb_fix, 2, 1)
        grid.addWidget(QLabel("\u2605 Satellite Count"), 3, 0)
        grid.addWidget(self.cb_sat, 3, 1)
        grid.addWidget(QLabel("\u23F0 Timestamp"), 4, 0)
        grid.addWidget(self.cb_ts, 4, 1)

        layout.addLayout(grid)

        self.plot_btn = QPushButton("\U0001F30D  Plot on Map")
        self.plot_btn.setStyleSheet(f"""
            QPushButton {{
                margin: 6px 14px; padding: 10px;
                background: linear-gradient(135deg, {DARK_ACCENT}, #3d7fd4);
                border: none; border-radius: 8px;
                color: white; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ filter: brightness(1.1); }}
            QPushButton:disabled {{ background: {DARK_SURFACE3}; color: {DARK_TEXT3}; }}
        """)
        self.plot_btn.clicked.connect(self.plot_data)
        self.plot_btn.setEnabled(False)
        layout.addWidget(self.plot_btn)

        section2 = QLabel("  Detected Columns")
        section2.setStyleSheet(f"padding: 10px 14px; font-size: 11px; font-weight: 600; color: {DARK_TEXT3}; letter-spacing: 0.8px; text-transform: uppercase; border-bottom: 1px solid {DARK_BORDER}; border-top: 1px solid {DARK_BORDER};")
        layout.addWidget(section2)

        self.col_preview = QLabel("Load a file to preview column headers.")
        self.col_preview.setStyleSheet(f"padding: 12px 14px; font-size: 12px; color: {DARK_TEXT3}; background: transparent;")
        self.col_preview.setWordWrap(True)
        layout.addWidget(self.col_preview, 1)

    def populate_combos(self, headers):
        for cb in [self.cb_lat, self.cb_lon, self.cb_fix, self.cb_sat, self.cb_ts]:
            current = cb.currentData()
            cb.clear()
            cb.addItem("\u2014 None \u2014", "")
            for h in headers:
                cb.addItem(h, h)
            if current and current in headers:
                cb.setCurrentIndex(cb.findData(current))

    def set_auto_detect(self, col_map):
        mapping = {
            self.cb_lat: col_map.get("lat", ""),
            self.cb_lon: col_map.get("lon", ""),
            self.cb_fix: col_map.get("fix", ""),
            self.cb_sat: col_map.get("sat", ""),
            self.cb_ts:  col_map.get("ts", ""),
        }
        for cb, val in mapping.items():
            idx = cb.findData(val)
            if idx >= 0:
                cb.setCurrentIndex(idx)
        self.plot_btn.setEnabled(True)

    def update_preview(self, headers):
        html = '<div style="display:flex; flex-wrap:wrap; gap:4px;">'
        for h in headers:
            html += f'<div style="background:{DARK_SURFACE2};border:1px solid {DARK_BORDER};border-radius:5px;padding:4px 8px;font-size:11px;color:{DARK_TEXT2};">{h}</div>'
        html += "</div>"
        self.col_preview.setText(html)
        self.col_preview.setTextFormat(Qt.RichText)

    def plot_data(self):
        lat_col = self.cb_lat.currentData()
        lon_col = self.cb_lon.currentData()
        if not lat_col or not lon_col:
            self.main_window.show_toast("Please map Latitude and Longitude columns", "error")
            return
        fix_col = self.cb_fix.currentData()
        sat_col = self.cb_sat.currentData()
        ts_col = self.cb_ts.currentData()

        self.data_model.parse_points(lat_col, lon_col, fix_col, sat_col, ts_col)
        points = self.data_model.points
        if not points:
            self.main_window.show_toast("No valid lat/lon data found", "error")
            return

        self.main_window.plot_points(points)

    def on_data_changed(self):
        pass


class ManualTab(QWidget):
    def __init__(self, data_model: GNSSData, main_window):
        super().__init__()
        self.data_model = data_model
        self.main_window = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.lat_edit = QLineEdit()
        self.lat_edit.setPlaceholderText("24.8607")
        form.addRow("Latitude", self.lat_edit)

        self.lon_edit = QLineEdit()
        self.lon_edit.setPlaceholderText("67.0011")
        form.addRow("Longitude", self.lon_edit)

        self.fix_combo = QComboBox()
        for val, label in sorted(FIX_LABELS.items()):
            self.fix_combo.addItem(f"{val} \u2014 {label}", val)
        self.fix_combo.setCurrentIndex(1)
        form.addRow("Fix Quality", self.fix_combo)

        self.sat_spin = QSpinBox()
        self.sat_spin.setRange(0, 99)
        self.sat_spin.setValue(8)
        form.addRow("Satellite Count", self.sat_spin)

        self.ts_edit = QDateTimeEdit()
        self.ts_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.ts_edit.setCalendarPopup(True)
        from PySide6.QtCore import QDateTime
        self.ts_edit.setDateTime(QDateTime.currentDateTime())
        form.addRow("Timestamp", self.ts_edit)

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Location label (optional)")
        form.addRow("Label", self.label_edit)

        layout.addLayout(form)

        self.add_btn = QPushButton("+  Add Point to Map")
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px;
                background: {DARK_SURFACE3};
                border: 1px solid {DARK_BORDER2};
                border-radius: 8px; color: {DARK_ACCENT2};
                font-size: 13px; font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(0,212,170,0.1);
                border-color: {DARK_ACCENT2};
            }}
        """)
        self.add_btn.clicked.connect(self.add_point)
        layout.addWidget(self.add_btn)

        layout.addStretch()

    def add_point(self):
        try:
            lat = float(self.lat_edit.text())
            lon = float(self.lon_edit.text())
        except ValueError:
            self.main_window.show_toast("Enter valid latitude and longitude", "error")
            return

        if lat < -90 or lat > 90 or lon < -180 or lon > 180:
            self.main_window.show_toast("Coordinates out of range", "error")
            return

        fix = self.fix_combo.currentData()
        sat = self.sat_spin.value()
        ts = self.ts_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        label = self.label_edit.text()

        self.data_model.add_manual_point(lat, lon, fix, sat, ts, label)
        self.main_window.plot_points(self.data_model.points)
        self.main_window.switch_to_tab(2)
        self.main_window.show_toast("Point added to map", "success")


class DataTab(QWidget):
    def __init__(self, data_model: GNSSData, main_window):
        super().__init__()
        self.data_model = data_model
        self.main_window = main_window
        self.data_model.data_changed.connect(self.refresh)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  Loaded Points")
        header.setStyleSheet(f"padding: 10px 14px; font-size: 11px; font-weight: 600; color: {DARK_TEXT3}; letter-spacing: 0.8px; text-transform: uppercase; border-bottom: 1px solid {DARK_BORDER};")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "Latitude", "Longitude", "Fix", "Sats", "Timestamp"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemClicked.connect(self.on_row_clicked)
        layout.addWidget(self.table)

        self.no_data = QLabel("No data points loaded yet.")
        self.no_data.setStyleSheet(f"padding: 24px; text-align: center; color: {DARK_TEXT3}; font-size: 13px; background: transparent;")
        self.no_data.setAlignment(Qt.AlignCenter)
        self.no_data.hide()
        layout.addWidget(self.no_data)

    def refresh(self):
        points = self.data_model.points
        if not points:
            self.table.setRowCount(0)
            self.table.hide()
            self.no_data.show()
            return

        self.table.show()
        self.no_data.hide()
        self.table.setRowCount(len(points))

        fix_colors = {
            0: (DARK_ACCENT3, "rgba(255,107,107,0.15)"),
            1: (DARK_ACCENT4, "rgba(255,217,61,0.15)"),
            2: (DARK_ACCENT2, "rgba(0,212,170,0.15)"),
            4: (DARK_ACCENT, "rgba(79,158,255,0.15)"),
            5: (DARK_ACCENT2, "rgba(0,212,170,0.15)"),
        }

        for i, p in enumerate(points):
            items = [
                QTableWidgetItem(str(p["index"])),
                QTableWidgetItem(f"{p['lat']:.5f}"),
                QTableWidgetItem(f"{p['lon']:.5f}"),
                QTableWidgetItem(FIX_LABELS.get(p["fix"], str(p["fix"]))),
                QTableWidgetItem(str(p["sat"]) if p["sat"] else "\u2014"),
                QTableWidgetItem(str(p["ts"])[:16] if p["ts"] else "\u2014"),
            ]
            for j, item in enumerate(items):
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(i, j, item)

            fc = fix_colors.get(p["fix"], (DARK_ACCENT4, "rgba(255,217,61,0.15)"))
            self.table.item(i, 3).setBackground(QColor(fc[1]))
            self.table.item(i, 3).setForeground(QColor(fc[0]))

        self.table.resizeColumnsToContents()

    def on_row_clicked(self, item):
        row = item.row()
        points = self.data_model.points
        if 0 <= row < len(points):
            p = points[row]
            self.main_window.show_info_panel(p)


class DetectTab(QWidget):
    def __init__(self, data_model: GNSSData, main_window):
        super().__init__()
        self.data_model = data_model
        self.main_window = main_window
        self.data_model.data_changed.connect(self.on_data_changed)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        params_header = QLabel("  Detection Parameters")
        params_header.setStyleSheet(f"padding: 10px 14px; font-size: 11px; font-weight: 600; color: {DARK_TEXT3}; letter-spacing: 0.8px; text-transform: uppercase; border-bottom: 1px solid {DARK_BORDER};")
        layout.addWidget(params_header)

        params_w = QWidget()
        params_w.setStyleSheet(f"background: transparent;")
        p_layout = QVBoxLayout(params_w)
        p_layout.setContentsMargins(14, 10, 14, 10)
        p_layout.setSpacing(6)

        def param_row(label, widget):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {DARK_TEXT2}; font-size: 12px; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(widget)
            p_layout.addLayout(row)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(1, 10000)
        self.speed_spin.setValue(100)
        self.speed_spin.setSuffix(" m/s")
        self.speed_spin.setStyleSheet(f"width: 90px; text-align: right;")
        param_row("Speed Threshold", self.speed_spin)

        self.outlier_spin = QDoubleSpinBox()
        self.outlier_spin.setRange(0.5, 10)
        self.outlier_spin.setValue(3.0)
        self.outlier_spin.setSingleStep(0.5)
        self.outlier_spin.setStyleSheet(f"width: 90px; text-align: right;")
        param_row("Outlier Std Devs", self.outlier_spin)

        self.sat_spin = QSpinBox()
        self.sat_spin.setRange(1, 20)
        self.sat_spin.setValue(4)
        self.sat_spin.setStyleSheet(f"width: 90px; text-align: right;")
        param_row("Min Satellites", self.sat_spin)

        self.fix_drop_check = QCheckBox("Fix quality drops")
        self.fix_drop_check.setChecked(True)
        self.fix_drop_check.setStyleSheet(f"color: {DARK_TEXT2}; font-size: 12px; background: transparent;")
        p_layout.addWidget(self.fix_drop_check)

        self.outlier_check = QCheckBox("Position outliers")
        self.outlier_check.setChecked(True)
        self.outlier_check.setStyleSheet(f"color: {DARK_TEXT2}; font-size: 12px; background: transparent;")
        p_layout.addWidget(self.outlier_check)

        self.low_sat_check = QCheckBox("Low satellite alerts")
        self.low_sat_check.setChecked(True)
        self.low_sat_check.setStyleSheet(f"color: {DARK_TEXT2}; font-size: 12px; background: transparent;")
        p_layout.addWidget(self.low_sat_check)

        layout.addWidget(params_w)

        self.run_btn = QPushButton("\U0001F4E1  Run Detection")
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                margin: 6px 14px; padding: 10px;
                background: linear-gradient(135deg, #e05fff, #9c3fff);
                border: none; border-radius: 8px;
                color: white; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ filter: brightness(1.1); }}
            QPushButton:disabled {{ background: {DARK_SURFACE3}; color: {DARK_TEXT3}; }}
        """)
        self.run_btn.clicked.connect(self.run_detection)
        layout.addWidget(self.run_btn)

        results_header = QLabel("  Detection Results")
        results_header.setStyleSheet(f"padding: 10px 14px; font-size: 11px; font-weight: 600; color: {DARK_TEXT3}; letter-spacing: 0.8px; text-transform: uppercase; border-bottom: 1px solid {DARK_BORDER}; border-top: 1px solid {DARK_BORDER};")
        layout.addWidget(results_header)

        self.summary_w = QWidget()
        self.summary_w.setStyleSheet("background: transparent;")
        self.summary_w.setMaximumHeight(80)
        s_layout = QHBoxLayout(self.summary_w)
        s_layout.setContentsMargins(14, 8, 14, 8)
        self.summary_w.hide()
        self.summary_w.setLayout(s_layout)
        layout.addWidget(self.summary_w)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

        self.no_data_label = QLabel("No detection results yet.\nLoad data and click Run Detection.")
        self.no_data_label.setStyleSheet(f"padding: 32px; text-align: center; color: {DARK_TEXT3}; font-size: 13px; background: transparent;")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.no_data_label)

    def run_detection(self):
        points = self.data_model.points
        if not points:
            self.main_window.show_toast("No data to analyze", "error")
            return

        speed_thresh = self.speed_spin.value()
        outlier_std = self.outlier_spin.value()
        min_sats = self.sat_spin.value()

        results = detect_anomalies(points, speed_thresh, outlier_std, min_sats)

        self.results_list.clear()
        self.no_data_label.hide()

        type_colors = {
            "anomaly": (DARK_ACCENT3, "rgba(255,107,107,0.08)", "rgba(255,107,107,0.3)"),
            "warning": (DARK_ACCENT4, "rgba(255,217,61,0.08)", "rgba(255,217,61,0.3)"),
            "info": (DARK_ACCENT, "rgba(79,158,255,0.08)", "rgba(79,158,255,0.3)"),
            "cluster": (DARK_ACCENT2, "rgba(0,212,170,0.08)", "rgba(0,212,170,0.3)"),
        }

        icons = {"anomaly": "\u26A0", "warning": "\u26A0", "info": "\u2139", "cluster": "\u2726"}

        anomalies = sum(1 for r in results if r["type"] == "anomaly")
        warnings = sum(1 for r in results if r["type"] == "warning")
        info = sum(1 for r in results if r["type"] in ("info", "cluster"))

        self.show_summary(anomalies, warnings, info)

        for r in results:
            tc = type_colors.get(r["type"], type_colors["info"])
            icon = icons.get(r["type"], "\u2139")

            w = QListWidgetItem()
            w.setData(Qt.UserRole, r)

            widget = QWidget()
            widget.setStyleSheet(f"background: transparent;")
            w_layout = QVBoxLayout(widget)
            w_layout.setContentsMargins(8, 6, 8, 6)
            w_layout.setSpacing(2)

            top = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"font-size: 14px; color: {tc[0]}; background: transparent;")
            top.addWidget(icon_lbl)

            title_lbl = QLabel(r["title"])
            title_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {tc[0]}; background: transparent;")
            top.addWidget(title_lbl, 1)

            if r.get("point_index"):
                idx_lbl = QLabel(f"#{r['point_index']}")
                idx_lbl.setStyleSheet(f"font-size: 10px; font-family: 'Consolas', monospace; padding: 1px 6px; border-radius: 8px; background: {tc[1]}; color: {tc[0]};")
                top.addWidget(idx_lbl)

            w_layout.addLayout(top)

            desc_lbl = QLabel(r["desc"])
            desc_lbl.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT3}; background: transparent;")
            desc_lbl.setWordWrap(True)
            w_layout.addWidget(desc_lbl)

            if r.get("severity", 0) > 0:
                sev = min(r["severity"] / 10, 1.0)
                bar_w = QWidget()
                bar_w.setStyleSheet("background: transparent;")
                bar_layout = QHBoxLayout(bar_w)
                bar_layout.setContentsMargins(22, 2, 0, 0)
                bar_bg = QFrame()
                bar_bg.setStyleSheet(f"background: {DARK_SURFACE3}; border-radius: 2px; height: 4px;")
                bar_bg.setFixedHeight(4)
                bar_fill = QFrame()
                bar_fill.setStyleSheet(f"background: {tc[0]}; border-radius: 2px; height: 4px;")
                bar_fill.setFixedWidth(int(100 * sev))
                bar_fill.setFixedHeight(4)
                bar_bg_layout = QHBoxLayout(bar_bg)
                bar_bg_layout.setContentsMargins(0, 0, 0, 0)
                bar_bg_layout.addWidget(bar_fill)
                bar_layout.addWidget(bar_bg, 1)
                w_layout.addLayout(bar_layout)

            w.setSizeHint(widget.sizeHint())
            self.results_list.addItem(w)
            self.results_list.setItemWidget(w, widget)

            if r.get("lat") is not None and r.get("lon") is not None:
                w.setToolTip(f"Click to locate: {r['lat']:.5f}, {r['lon']:.5f}")

        self.results_list.itemClicked.connect(self.on_result_clicked)

    def show_summary(self, anomalies, warnings, info):
        self.summary_w.show()
        layout = self.summary_w.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().deleteLater()

        for label, value, color in [
            ("Anomalies", str(anomalies), DARK_ACCENT3),
            ("Warnings", str(warnings), DARK_ACCENT4),
            ("Info", str(info), DARK_ACCENT),
        ]:
            card = QFrame()
            card.setStyleSheet(f"background: {DARK_SURFACE2}; border: 1px solid {DARK_BORDER}; border-radius: 8px;")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 6, 10, 6)
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"font-size: 22px; font-weight: 700; font-family: 'Consolas', monospace; color: {color}; background: transparent;")
            c_layout.addWidget(val_lbl)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 10px; color: {DARK_TEXT3}; text-transform: uppercase; letter-spacing: 0.4px; background: transparent;")
            c_layout.addWidget(lbl)
            layout.addWidget(card)

    def on_result_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data and data.get("lat") is not None:
            self.main_window.center_map(data["lat"], data["lon"])

    def on_data_changed(self):
        self.results_list.clear()
        self.summary_w.hide()
        self.no_data_label.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_model = GNSSData()
        self.setWindowTitle("GPS Location Estimator  \u2014  Desktop Edition")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        self.setStyleSheet(STYLESHEET)

        self._setup_menu()
        self._setup_ui()

        self.data_model.data_changed.connect(self._on_data_changed)

        QTimer.singleShot(500, self.load_demo)

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{ background: {DARK_SURFACE}; border-bottom: 1px solid {DARK_BORDER}; padding: 2px; }}
            QMenuBar::item {{ padding: 4px 12px; color: {DARK_TEXT2}; font-size: 12px; }}
            QMenuBar::item:selected {{ background: {DARK_SURFACE3}; color: {DARK_TEXT}; }}
            QMenu {{ background: {DARK_SURFACE2}; border: 1px solid {DARK_BORDER2}; }}
            QMenu::item {{ padding: 6px 24px; color: {DARK_TEXT2}; font-size: 12px; }}
            QMenu::item:selected {{ background: {DARK_SURFACE3}; color: {DARK_TEXT}; }}
        """)

        file_menu = menubar.addMenu("File")
        open_action = QAction("Open File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.browse_file)
        file_menu.addAction(open_action)

        export_action = QAction("Export CSV...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        demo_action = QAction("Load Demo Data", self)
        demo_action.triggered.connect(self.load_demo)
        file_menu.addAction(demo_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        fit_action = QAction("Fit All Points", self)
        fit_action.setShortcut("Ctrl+F")
        fit_action.triggered.connect(self.fit_bounds)
        view_menu.addAction(fit_action)

        clear_action = QAction("Clear All", self)
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self.clear_all)
        view_menu.addAction(clear_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet(f"background: {DARK_SURFACE}; border-bottom: 1px solid {DARK_BORDER};")
        title_bar.setFixedHeight(48)
        t_layout = QHBoxLayout(title_bar)
        t_layout.setContentsMargins(16, 0, 16, 0)

        logo = QLabel("\U0001F4E1  GPS Location Estimator")
        logo.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {DARK_TEXT}; background: transparent;")
        t_layout.addWidget(logo)

        ver = QLabel("v1.0.0")
        ver.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT3}; font-family: 'Consolas', monospace; background: transparent;")
        t_layout.addWidget(ver)

        t_layout.addStretch()

        self.status_dot = QLabel("\u25CF")
        self.status_dot.setStyleSheet(f"font-size: 10px; color: {DARK_TEXT3}; background: transparent;")
        t_layout.addWidget(self.status_dot)

        self.status_text = QLabel("No data loaded")
        self.status_text.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT2}; background: transparent;")
        t_layout.addWidget(self.status_text)

        main_layout.addWidget(title_bar)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        main_layout.addWidget(splitter, 1)

        # Left panel
        left_panel = QWidget()
        left_panel.setMinimumWidth(320)
        left_panel.setMaximumWidth(400)
        left_panel.setStyleSheet(f"background: {DARK_SURFACE}; border-right: 1px solid {DARK_BORDER};")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setStyleSheet(f"""
            QTabBar::tab {{ padding: 10px 12px; font-size: 11px; background: transparent; color: {DARK_TEXT3}; border-bottom: 2px solid transparent; text-transform: uppercase; letter-spacing: 0.3px; }}
            QTabBar::tab:selected {{ color: {DARK_ACCENT}; border-bottom-color: {DARK_ACCENT}; background: rgba(79,158,255,0.05); }}
            QTabBar::tab:hover {{ color: {DARK_TEXT2}; }}
        """)
        left_layout.addWidget(self.tabs)

        self.import_tab = ImportTab(self.data_model, self)
        self.manual_tab = ManualTab(self.data_model, self)
        self.data_tab = DataTab(self.data_model, self)
        self.detect_tab = DetectTab(self.data_model, self)

        self.tabs.addTab(self.import_tab, "Import")
        self.tabs.addTab(self.manual_tab, "Manual")
        self.tabs.addTab(self.data_tab, "Data")
        self.tabs.addTab(self.detect_tab, "Detect")

        splitter.addWidget(left_panel)

        # Right area
        right_area = QWidget()
        right_area.setStyleSheet(f"background: {DARK_BG};")
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Stats bar
        stats_bar = QWidget()
        stats_bar.setStyleSheet(f"background: {DARK_SURFACE}; border-bottom: 1px solid {DARK_BORDER};")
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(0)

        self.stat_total = StatsCard("Total Points", "0", "loaded")
        self.stat_valid = StatsCard("Valid Fix", "0", "quality \u2265 1", DARK_ACCENT2)
        self.stat_avg_sat = StatsCard("Avg Satellites", "\u2014", "per point")
        self.stat_center = StatsCard("Est. Center", "\u2014", "weighted mean")
        self.stat_span = StatsCard("Coverage Span", "\u2014", "bounding box")

        stats_layout.addWidget(self.stat_total)
        stats_layout.addWidget(self.stat_valid)
        stats_layout.addWidget(self.stat_avg_sat)
        stats_layout.addWidget(self.stat_center)
        stats_layout.addWidget(self.stat_span)

        right_layout.addWidget(stats_bar)

        # Map
        self.map_widget = MapWidget()
        right_layout.addWidget(self.map_widget, 1)

        # Bottom bar
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet(f"background: {DARK_SURFACE}; border-top: 1px solid {DARK_BORDER};")
        bottom_bar.setFixedHeight(36)
        b_layout = QHBoxLayout(bottom_bar)
        b_layout.setContentsMargins(14, 0, 14, 0)

        info_lbl = QLabel("\u2139 Auto-detects column names: lat/lon/fix/sat/time variants")
        info_lbl.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT3}; background: transparent;")
        b_layout.addWidget(info_lbl)

        b_layout.addStretch()

        self.footer_points = QLabel("0 points on map")
        self.footer_points.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT2}; background: transparent;")
        b_layout.addWidget(self.footer_points)

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {DARK_BORDER}; background: transparent;")
        b_layout.addWidget(sep)

        self.footer_center = QLabel("Center: \u2014")
        self.footer_center.setStyleSheet(f"font-size: 11px; color: {DARK_TEXT2}; font-family: 'Consolas', monospace; background: transparent;")
        b_layout.addWidget(self.footer_center)

        right_layout.addWidget(bottom_bar)

        splitter.addWidget(right_area)
        splitter.setSizes([340, splitter.width() - 340])

        self.toast_label = QLabel(self)
        self.toast_label.setStyleSheet(f"""
            QLabel {{
                background: {DARK_SURFACE3}; border: 1px solid {DARK_BORDER2};
                border-radius: 8px; padding: 10px 16px; font-size: 13px;
                color: {DARK_TEXT};
            }}
        """)
        self.toast_label.setVisible(False)
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(lambda: self.toast_label.setVisible(False))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast_label.isVisible():
            self._position_toast()

    def _position_toast(self):
        self.toast_label.adjustSize()
        x = self.width() - self.toast_label.width() - 20
        y = self.height() - 60
        self.toast_label.move(x, y)

    def show_toast(self, msg, type_=""):
        icons = {"success": "\u2714", "error": "\u2718", "": "\u2139"}
        colors = {"success": DARK_ACCENT2, "error": DARK_ACCENT3, "": DARK_ACCENT}
        icon = icons.get(type_, "\u2139")
        color = colors.get(type_, DARK_ACCENT)
        self.toast_label.setText(f'{icon}  {msg}')
        border_color = {"success": DARK_ACCENT2, "error": DARK_ACCENT3, "": DARK_ACCENT}.get(type_, DARK_BORDER2)
        self.toast_label.setStyleSheet(f"""
            QLabel {{
                background: {DARK_SURFACE3}; border: 1px solid {border_color};
                border-radius: 8px; padding: 10px 16px; font-size: 13px;
                color: {DARK_TEXT};
            }}
        """)
        self.toast_label.adjustSize()
        self._position_toast()
        self.toast_label.setVisible(True)
        self.toast_timer.start(3000)

    def load_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            self.show_toast(f"Unsupported format: {ext}", "error")
            return

        try:
            df = self.data_model.load_file(filepath)
        except Exception as e:
            self.show_toast(f"Error reading file: {e}", "error")
            return

        headers = self.data_model.raw_headers
        col_map = self.data_model.column_map
        self.import_tab.populate_combos(headers)
        self.import_tab.set_auto_detect(col_map)
        self.import_tab.update_preview(headers)

        # Auto-plot if lat/lon columns detected
        lat_col = col_map.get("lat", "")
        lon_col = col_map.get("lon", "")
        if lat_col and lon_col:
            fix_col = col_map.get("fix", "")
            sat_col = col_map.get("sat", "")
            ts_col = col_map.get("ts", "")
            self.data_model.parse_points(lat_col, lon_col, fix_col, sat_col, ts_col)
            points = self.data_model.points
            if points:
                self.plot_points(points)
                self.show_toast(
                    f"Loaded {len(df)} rows \u2014 "
                    f"auto-plotted {len(points)} points from {os.path.basename(filepath)}",
                    "success"
                )
                return

        self.show_toast(f"Loaded {len(df)} rows from {os.path.basename(filepath)}", "success")
        self.tabs.setCurrentIndex(0)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open GNSS Data File", "",
            "Data Files (*.csv *.txt *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;Text Files (*.txt);;All Files (*.*)"
        )
        if path:
            self.load_file(path)

    def plot_points(self, points):
        self.map_widget.update_map(points)
        self._update_stats()
        self.tabs.setCurrentIndex(2)

    def _update_stats(self):
        stats = self.data_model.compute_stats()
        points = self.data_model.points
        n = stats["total"]

        self.stat_total.set_value(str(n))
        self.footer_points.setText(f"{n} points on map")

        if n == 0:
            self.stat_valid.set_value("0", DARK_ACCENT2)
            self.stat_avg_sat.set_value("\u2014")
            self.stat_center.set_value("\u2014")
            self.stat_span.set_value("\u2014")
            self.footer_center.setText("Center: \u2014")
            self.set_status("", "No data loaded")
            return

        self.stat_valid.set_value(str(stats["valid"]), DARK_ACCENT2)
        self.stat_avg_sat.set_value(f"{stats['avg_sat']:.1f}")

        if stats["center"]:
            c = stats["center"]
            center_text = f"{c['lat']:.4f}, {c['lon']:.4f}"
            self.stat_center.set_value(center_text)
            self.footer_center.setText(f"Center: {c['lat']:.5f}, {c['lon']:.5f}")
        else:
            self.stat_center.set_value("\u2014")
            self.footer_center.setText("Center: \u2014")

        span_text = f"{stats['lat_span']:.4f}\u00b0 \u00d7 {stats['lon_span']:.4f}\u00b0"
        self.stat_span.set_value(span_text)

        if stats["valid"] == n:
            self.set_status("active", f"{n} points loaded \u2014 all valid")
        elif stats["valid"] > 0:
            self.set_status("warn", f"{stats['valid']}/{n} valid fixes")
        else:
            self.set_status("bad", f"All {n} points are invalid (fix=0)")

    def set_status(self, type_, text):
        colors = {"active": DARK_ACCENT2, "warn": DARK_ACCENT4, "bad": DARK_ACCENT3, "": DARK_TEXT3}
        color = colors.get(type_, DARK_TEXT3)
        self.status_dot.setStyleSheet(f"font-size: 10px; color: {color}; background: transparent;")
        self.status_text.setText(text)

    def show_info_panel(self, point):
        center = self.data_model.compute_center()
        self.map_widget.update_map(self.data_model.points)
        self.map_widget.page().runJavaScript(
            f"var p = DATA.find(d => d.index === {point['index']}); if (p) {{ map.setView([p.lat, p.lon], 16); }}"
        )
        self.show_toast(f"Point #{point['index']}: {point['lat']:.5f}, {point['lon']:.5f}", "")

    def center_map(self, lat, lon):
        self.map_widget.page().runJavaScript(f"map.setView([{lat}, {lon}], 16);")

    def fit_bounds(self):
        if self.data_model.points:
            self.map_widget.page().runJavaScript("fitBounds();")

    def clear_all(self):
        self.data_model.clear()
        self.map_widget.update_map([])
        self.stat_total.set_value("0")
        self.stat_valid.set_value("0", DARK_ACCENT2)
        self.stat_avg_sat.set_value("\u2014")
        self.stat_center.set_value("\u2014")
        self.stat_span.set_value("\u2014")
        self.footer_points.setText("0 points on map")
        self.footer_center.setText("Center: \u2014")
        self.set_status("", "No data loaded")
        self.show_toast("Map cleared", "")

    def export_data(self):
        if not self.data_model.points:
            self.show_toast("No data to export", "error")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "gps_locations.csv", "CSV Files (*.csv)")
        if path:
            self.data_model.export_csv(path)
            self.show_toast("Data exported as CSV", "success")

    def load_demo(self):
        demo = [
            {"lat": 24.8607, "lon": 67.0011, "fix": 1, "sat": 8, "ts": "2024-03-15 08:00:00", "label": "", "estimated": False, "index": 1},
            {"lat": 24.8615, "lon": 67.0020, "fix": 2, "sat": 10, "ts": "2024-03-15 08:05:00", "label": "", "estimated": False, "index": 2},
            {"lat": 24.8598, "lon": 67.0005, "fix": 1, "sat": 7, "ts": "2024-03-15 08:10:00", "label": "", "estimated": False, "index": 3},
            {"lat": 24.8630, "lon": 67.0035, "fix": 4, "sat": 12, "ts": "2024-03-15 08:15:00", "label": "", "estimated": False, "index": 4},
            {"lat": 24.8590, "lon": 66.9998, "fix": 0, "sat": 3, "ts": "2024-03-15 08:20:00", "label": "", "estimated": True, "index": 5},
            {"lat": 24.8620, "lon": 67.0025, "fix": 1, "sat": 9, "ts": "2024-03-15 08:25:00", "label": "", "estimated": False, "index": 6},
            {"lat": 24.8640, "lon": 67.0045, "fix": 2, "sat": 11, "ts": "2024-03-15 08:30:00", "label": "", "estimated": False, "index": 7},
            {"lat": 24.8580, "lon": 66.9990, "fix": 1, "sat": 8, "ts": "2024-03-15 08:35:00", "label": "", "estimated": False, "index": 8},
        ]
        self.data_model.points = demo
        self.data_model.data_changed.emit()
        self.plot_points(demo)
        self.show_toast("Demo data loaded \u2014 8 GPS points in Karachi", "success")

    def switch_to_tab(self, index):
        self.tabs.setCurrentIndex(index)

    def _on_data_changed(self):
        self._update_stats()
