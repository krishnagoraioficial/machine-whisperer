# ---------------------------------------------------------
# FILE: ui_dashboard.py
# AUTHOR: Krishna Gorai (Roll No: 25f1100001)
# PURPOSE: Frontend layout for MachineWhisperer. Displays DSP analytics 
#          and sets up UI placeholders for Phase 2 ML anomaly classification.
# # ---------------------------------------------------------
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QPushButton, QComboBox, QFrame, QGridLayout)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class DashboardUI:
    def __init__(self):
        # Configure PyQtGraph global colors BEFORE creating the window
        pg.setConfigOptions(background='#111A22', foreground='#81909D')

        self.main_window = QWidget()
        self.main_window.setWindowTitle("MachineWhisperer - Predictive Maintenance Dashboard")
        self.main_window.resize(1200, 950)
        
        # Main App Styling (QSS)
        self.main_window.setStyleSheet("""
            QWidget {
                background-color: #0B1117;
                color: #E8EEF3;
                font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            }
            QFrame.card {
                background-color: #111A22;
                border: 1px solid #24313D;
                border-radius: 12px;
            }
            QLabel.title { font-size: 20px; font-weight: bold; color: #E8EEF3; }
            QLabel.subtitle { font-size: 13px; color: #81909D; }
            QLabel.kpi_title { font-size: 12px; font-weight: bold; color: #81909D; text-transform: uppercase; }
            QLabel.kpi_value { font-size: 28px; font-weight: bold; color: #20D6E8; }
            QLabel.kpi_status { font-size: 11px; color: #35D07F; }
            QComboBox, QSpinBox {
                background-color: #151F28;
                border: 1px solid #24313D;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #24313D;
                color: #20D6E8;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #20D6E8; color: #0B1117; }
        """)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.main_window.setLayout(self.layout)

        # ---------------------------------------------------------
        # 1. TOP HEADER
        # ---------------------------------------------------------
        header_layout = QHBoxLayout()
        
        info_layout = QVBoxLayout()
        title = QLabel("MACHINE WHISPERER")
        title.setProperty("class", "title")
        subtitle = QLabel("Distributed Acoustic Sensing • Predictive Machinery Maintenance\nAuthor: Krishna Gorai (25f1100001) | IITM BS-ES")
        subtitle.setProperty("class", "subtitle")
        info_layout.addWidget(title)
        info_layout.addWidget(subtitle)
        
        machine_layout = QVBoxLayout()
        machine_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.machine_selector = QComboBox()
        self.machine_selector.addItems(["M-01 • CNC Motor", "M-02 • Hydraulic Pump", "M-03 • Heavy Compressor"])
        self.machine_selector.setFixedWidth(200)
        
        status_label = QLabel("● LIVE  |  Scan Active")
        status_label.setStyleSheet("color: #35D07F; font-weight: bold;")
        
        machine_layout.addWidget(self.machine_selector)
        machine_layout.addWidget(status_label, alignment=Qt.AlignmentFlag.AlignRight)

        header_layout.addLayout(info_layout)
        header_layout.addLayout(machine_layout)
        self.layout.addLayout(header_layout)

        # ---------------------------------------------------------
        # 2. KPI HEALTH CARDS
        # ---------------------------------------------------------
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        # Helper function to generate KPI cards
        def create_kpi_card(title_text, default_val, default_status):
            card = QFrame()
            card.setProperty("class", "card")
            card_layout = QVBoxLayout(card)
            
            lbl_title = QLabel(title_text)
            lbl_title.setProperty("class", "kpi_title")
            lbl_val = QLabel(default_val)
            lbl_val.setProperty("class", "kpi_value")
            lbl_status = QLabel(default_status)
            lbl_status.setProperty("class", "kpi_status")
            
            card_layout.addWidget(lbl_title)
            card_layout.addWidget(lbl_val)
            card_layout.addWidget(lbl_status)
            return card, lbl_val, lbl_status

        card_health, self.lbl_health_val, self.lbl_health_stat = create_kpi_card("MACHINE HEALTH", "98 / 100", "██████████░ NORMAL")
        card_rms, self.lbl_rms_val, self.lbl_rms_stat = create_kpi_card("RMS ENERGY", "0.000 g", "Stable Baseline")
        card_freq, self.lbl_freq_val, self.lbl_freq_stat = create_kpi_card("DOMINANT FREQUENCY", "0 Hz", "Normal Operating Band")
        card_sys, self.lbl_sys_val, self.lbl_sys_stat = create_kpi_card("SYSTEM STATUS", "● NORMAL", "No anomalies detected")
        self.lbl_sys_val.setStyleSheet("color: #35D07F;") # Force green

        kpi_layout.addWidget(card_health)
        kpi_layout.addWidget(card_rms)
        kpi_layout.addWidget(card_freq)
        kpi_layout.addWidget(card_sys)
        self.layout.addLayout(kpi_layout)

        # ---------------------------------------------------------
        # 3. ANOMALY PANEL & FILTER CONTROLS
        # ---------------------------------------------------------
        middle_ctrl_layout = QHBoxLayout()
        middle_ctrl_layout.setSpacing(16)
        
        # Anomaly Panel
        self.anomaly_card = QFrame()
        self.anomaly_card.setProperty("class", "card")
        anomaly_layout = QVBoxLayout(self.anomaly_card)
        self.anomaly_title = QLabel("ANOMALY DETECTION")
        self.anomaly_title.setProperty("class", "kpi_title")
        self.anomaly_status = QLabel("✓ No significant anomalies detected")
        self.anomaly_status.setStyleSheet("color: #35D07F; font-size: 14px; font-weight: bold;")
        anomaly_layout.addWidget(self.anomaly_title)
        anomaly_layout.addWidget(self.anomaly_status)
        middle_ctrl_layout.addWidget(self.anomaly_card, stretch=2)

        # Filters
        filter_card = QFrame()
        filter_card.setProperty("class", "card")
        filter_layout = QHBoxLayout(filter_card)
        
        filter_layout.addWidget(QLabel("Low Cut (Hz):"))
        self.lowcut_input = QSpinBox()
        self.lowcut_input.setRange(10, 7999)
        self.lowcut_input.setValue(80)
        filter_layout.addWidget(self.lowcut_input)

        filter_layout.addWidget(QLabel("High Cut (Hz):"))
        self.highcut_input = QSpinBox()
        self.highcut_input.setRange(20, 8000)
        self.highcut_input.setValue(3000)
        filter_layout.addWidget(self.highcut_input)

        self.apply_btn = QPushButton("APPLY FILTER")
        filter_layout.addWidget(self.apply_btn)
        middle_ctrl_layout.addWidget(filter_card, stretch=3)
        
        self.layout.addLayout(middle_ctrl_layout)

        # ---------------------------------------------------------
        # 4. DATA VISUALIZATION (PYQTGRAPH)
        # ---------------------------------------------------------
        graph_card = QFrame()
        graph_card.setProperty("class", "card")
        graph_layout = QVBoxLayout(graph_card)
        
        self.window = pg.GraphicsLayoutWidget()
        graph_layout.addWidget(self.window)
        self.layout.addWidget(graph_card, stretch=1)

        # Spectrogram
        self.spectrogram_plot = self.window.addPlot(title="CONTINUOUS SPECTROGRAM (Frequency Activity)", row=0, col=0)
        self.image_item = pg.ImageItem()
        self.spectrogram_plot.addItem(self.image_item)
        self.image_item.setColorMap(pg.colormap.get('inferno'))
        self.image_item.setLevels((-30, 40))

        # Waveform
        self.waveform_plot = self.window.addPlot(title="LIVE ACOUSTIC SIGNAL (Filtered)", row=1, col=0)
        self.waveform_plot.setYRange(-0.5, 0.5)
        self.waveform_plot.showGrid(x=True, y=True, alpha=0.2)
        self.waveform_curve = self.waveform_plot.plot(pen=pg.mkPen('#20D6E8', width=1.5)) 

        # RMS Trend
        self.rms_plot = self.window.addPlot(title="MACHINE HEALTH TREND (RMS Energy)", row=2, col=0)
        self.rms_plot.setYRange(0, 0.2)
        self.rms_plot.showGrid(x=True, y=True, alpha=0.2)
        self.rms_curve = self.rms_plot.plot(pen=pg.mkPen('#F5B942', width=2), fillLevel=0, brush=(245, 185, 66, 50)) 

    def show(self):
        self.main_window.show()

    def update_kpis(self, rms_val, dom_freq, is_anomaly):
        """Updates the text on the top KPI cards based on backend math."""
        self.lbl_rms_val.setText(f"{rms_val:.4f} g")
        self.lbl_freq_val.setText(f"{dom_freq:.0f} Hz")
        
        if is_anomaly:
            self.lbl_health_val.setText("Coming Soon...")
            self.lbl_health_val.setStyleSheet("color: #FF4D5A; font-size: 28px; font-weight: bold;")
            self.lbl_health_stat.setText("████░░░░░░ CRITICAL")
            self.lbl_health_stat.setStyleSheet("color: #FF4D5A; font-size: 11px;")
            
            self.lbl_sys_val.setText("🔴 CRITICAL")
            self.lbl_sys_val.setStyleSheet("color: #FF4D5A; font-size: 28px; font-weight: bold;")
            self.lbl_sys_stat.setText("Coming Soon...")
            
            self.anomaly_card.setStyleSheet("QFrame.card { border: 2px solid #FF4D5A; background-color: #1a0a0c; }")
            self.anomaly_status.setText("Coming Soon...")
            self.anomaly_status.setStyleSheet("color: #FF4D5A; font-size: 14px; font-weight: bold;")
            self.rms_curve.setPen(pg.mkPen('#FF4D5A', width=2))
        else:
            self.lbl_health_val.setText("Coming Soon...")
            self.lbl_health_val.setStyleSheet("color: #35D07F; font-size: 28px; font-weight: bold;")
            self.lbl_health_stat.setText("██████████░ NORMAL")
            self.lbl_health_stat.setStyleSheet("color: #35D07F; font-size: 11px;")
            
            self.lbl_sys_val.setText("● NORMAL")
            self.lbl_sys_val.setStyleSheet("color: #35D07F; font-size: 28px; font-weight: bold;")
            self.lbl_sys_stat.setText("Coming Soon...")
            
            self.anomaly_card.setStyleSheet("QFrame.card { background-color: #111A22; border: 1px solid #24313D; }")
            self.anomaly_status.setText("Coming Soon...")
            self.anomaly_status.setStyleSheet("color: #35D07F; font-size: 14px; font-weight: bold;")
            self.rms_curve.setPen(pg.mkPen('#35D07F', width=2))