from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import QEasingCurve, QDateTime, QPropertyAnimation, QRect, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QColor
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)

from smart_home import SmartHomeService


BG = "#020305"
PANEL = "#07080b"
PANEL_2 = "#0d0f14"
ACCENT = "#ffb300"
ACCENT_SOFT = "rgba(255, 179, 0,0.12)"
ACCENT_LINE = "rgba(255, 179, 0,0.22)"
TEXT = "#ffffff"
TEXT_MED = "rgba(255,255,255,0.85)"
TEXT_DIM = "rgba(255,255,255,0.65)"
GREEN = "#37ff5f"


@dataclass(frozen=True)
class PlatformRow:
    key: str
    name: str
    available: bool
    auth_fields: list[tuple[str, str, str, bool]]


class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


def _panel_style(border_alpha: int = 34) -> str:
    alpha = border_alpha / 255.0
    return (
        "QFrame { "
        "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(16, 18, 26, 0.75), stop:1 rgba(8, 10, 15, 0.88)); "
        f"border: 1.5px solid rgba(255, 179, 0, {alpha:.3f}); "
        "border-radius: 18px; "
        "}"
    )


def _soft_button_style() -> str:
    return (
        f"QPushButton {{ background: rgba(255,255,255,0.03); color: {TEXT}; "
        "border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0 12px; }}"
        f"QPushButton:hover {{ border: 1px solid {ACCENT}; background: rgba(255, 179, 0,0.08); }}"
    )


class AddDeviceDialog(QDialog):
    def __init__(self, service: SmartHomeService, parent=None):
        super().__init__(parent)
        self._service = service
        self._provider_key: str | None = None
        self._provider_label = ""
        self._preview: dict[str, Any] = {}
        self._result: dict[str, Any] = {}
        self._fields: dict[str, QLineEdit] = {}
        self._checks: list[tuple[str, QCheckBox]] = []
        self._platform_buttons: list[ClickableFrame] = []

        self.setWindowTitle("Add Device")
        self.setModal(True)
        self.setMinimumSize(780, 620)
        self.setStyleSheet(
            f"""
            QDialog {{ background: {BG}; color: {TEXT}; }}
            QLabel {{ background: transparent; }}
            QLineEdit, QComboBox {{
                background: rgba(255,255,255,0.04);
                color: {TEXT};
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
                min-height: 34px;
                padding: 0 10px;
            }}
            QScrollArea {{ background: transparent; border: none; }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("ADD DEVICE")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Black))
        title.setStyleSheet(f"color: {TEXT}; letter-spacing: 2px;")
        sub = QLabel("Choose a platform, authenticate, scan, and save your devices locally.")
        sub.setStyleSheet(f"color: {TEXT_DIM};")
        root.addWidget(title)
        root.addWidget(sub)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_platform_page())
        self._stack.addWidget(self._build_auth_page())
        self._stack.addWidget(self._build_scan_page())
        self._stack.addWidget(self._build_finish_page())
        root.addWidget(self._stack, 1)

        row = QHBoxLayout()
        row.addStretch(1)
        self._back_btn = QPushButton("Back")
        self._next_btn = QPushButton("Next")
        self._cancel_btn = QPushButton("Cancel")
        for btn in (self._back_btn, self._next_btn, self._cancel_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(_soft_button_style())
        self._back_btn.clicked.connect(self._go_back)
        self._next_btn.clicked.connect(self._go_next)
        self._cancel_btn.clicked.connect(self.reject)
        row.addWidget(self._back_btn)
        row.addWidget(self._next_btn)
        row.addWidget(self._cancel_btn)
        root.addLayout(row)
        self._sync_buttons()

    def result_payload(self) -> dict[str, Any]:
        return dict(self._result)

    def _card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(_panel_style(40))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {TEXT};")
        lay.addWidget(lbl)
        return frame

    def _brand_glyph(self, key: str) -> str:
        return {
            "atomberg": "🌀",
            "kasa": "🔌",
            "hue": "💡",
            "lg": "📺",
            "daikin": "❄️",
            "tuya": "⚙️",
            "nest": "🏠",
            "smartthings": "📡"
        }.get(key, "⚙️")

    def _build_platform_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(self._card("Step 1: Choose Platform"))

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        
        for idx, platform in enumerate(self._platforms()):
            card = ClickableFrame()
            card.setObjectName(f"PlatformCard_{platform.key}")
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            
            lay_c = QHBoxLayout(card)
            lay_c.setContentsMargins(14, 12, 14, 12)
            lay_c.setSpacing(12)
            
            badge = QLabel(self._brand_glyph(platform.key))
            badge.setFixedSize(36, 36)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFont(QFont("Segoe UI", 13))
            
            badge_style = {
                "atomberg": "background: rgba(53, 255, 117, 0.08); color: #35ff75; border: 1px solid rgba(53, 255, 117, 0.2); border-radius: 18px;",
                "kasa": "background: rgba(0, 180, 216, 0.08); color: #00b4d8; border: 1px solid rgba(0, 180, 216, 0.2); border-radius: 18px;",
                "hue": "background: rgba(255, 165, 0, 0.08); color: #ffa500; border: 1px solid rgba(255, 165, 0, 0.2); border-radius: 18px;",
                "lg": "background: rgba(165, 0, 165, 0.08); color: #a500a5; border: 1px solid rgba(165, 0, 165, 0.2); border-radius: 18px;",
                "daikin": "background: rgba(123, 211, 247, 0.08); color: #7bd3f7; border: 1px solid rgba(123, 211, 247, 0.2); border-radius: 18px;",
                "tuya": "background: rgba(255, 90, 95, 0.08); color: #ff5a5f; border: 1px solid rgba(255, 90, 95, 0.2); border-radius: 18px;",
                "nest": "background: rgba(255, 255, 255, 0.05); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 18px;",
                "smartthings": "background: rgba(0, 100, 255, 0.08); color: #0064ff; border: 1px solid rgba(0, 100, 255, 0.2); border-radius: 18px;",
            }.get(platform.key, "background: rgba(255, 255, 255, 0.05); color: #ffffff; border-radius: 18px;")
            badge.setStyleSheet(badge_style)
            lay_c.addWidget(badge)
            
            text_lay = QVBoxLayout()
            text_lay.setSpacing(2)
            
            p_name = QLabel(platform.name)
            p_name.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            p_name.setStyleSheet("color: #ffffff; border: none;")
            
            subtitle = {
                "atomberg": "Ceiling fans & smart air flow",
                "kasa": "Plugs, switches, & smart sockets",
                "hue": "Smart lights, strips, & hue sync",
                "lg": "LG webOS smart TVs & apps",
                "daikin": "Split ACs & climate controls",
                "tuya": "IoT switches & generic appliances",
                "nest": "Thermostats & home security",
                "smartthings": "Samsung hub & IoT integrations",
            }.get(platform.key, "Smart home cloud connection")
            p_sub = QLabel(subtitle)
            p_sub.setFont(QFont("Segoe UI", 8))
            p_sub.setStyleSheet("color: rgba(255, 255, 255, 0.45); border: none;")
            
            text_lay.addWidget(p_name)
            text_lay.addWidget(p_sub)
            lay_c.addLayout(text_lay, 1)
            
            card.setMinimumHeight(64)
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 14px;
                }
                QFrame:hover {
                    background: rgba(255, 179, 0, 0.04);
                    border: 1px solid rgba(255, 179, 0, 0.3);
                }
            """)
            
            # Setup lambda for click
            card.clicked.connect(lambda key=platform.key, label=platform.name: self._choose_provider(key, label))
            self._platform_buttons.append(card)
            grid.addWidget(card, idx // 2, idx % 2)
            
        lay.addWidget(grid_host)
        return page

    def _build_auth_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(self._card("Step 2: Authenticate"))
        self._auth_desc = QLabel("Select a platform to build the right authentication form.")
        self._auth_desc.setStyleSheet(f"color: {TEXT_DIM};")
        lay.addWidget(self._auth_desc)
        self._auth_form_host = QFrame()
        self._auth_form_host.setStyleSheet("background: transparent;")
        self._auth_form = QFormLayout(self._auth_form_host)
        self._auth_form.setContentsMargins(12, 0, 12, 12)
        self._auth_form.setVerticalSpacing(10)
        lay.addWidget(self._auth_form_host)
        return page

    def _build_scan_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(self._card("Step 3: Scan"))
        self._scan_label = QLabel("Searching for devices...")
        self._scan_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._scan_label.setStyleSheet(f"color: {TEXT};")
        lay.addWidget(self._scan_label)
        self._scan_bar = QProgressBar()
        self._scan_bar.setRange(0, 100)
        self._scan_bar.setValue(12)
        self._scan_bar.setTextVisible(False)
        self._scan_bar.setFixedHeight(10)
        self._scan_bar.setStyleSheet(
            f"QProgressBar {{ background: rgba(255,255,255,0.05); border: none; border-radius: 4px; }} "
            f"QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}"
        )
        lay.addWidget(self._scan_bar)
        self._scan_scroll = QScrollArea()
        self._scan_scroll.setWidgetResizable(True)
        self._scan_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scan_host = QWidget()
        self._scan_host.setStyleSheet("background: transparent;")
        self._scan_list = QVBoxLayout(self._scan_host)
        self._scan_list.setSpacing(10)
        self._scan_list.addStretch(1)
        self._scan_scroll.setWidget(self._scan_host)
        lay.addWidget(self._scan_scroll, 1)
        return page

    def _build_finish_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(self._card("Step 4: Finish"))
        self._finish_summary = QLabel("")
        self._finish_summary.setWordWrap(True)
        self._finish_summary.setStyleSheet(f"color: {TEXT_MED};")
        lay.addWidget(self._finish_summary)
        return page

    def _platforms(self) -> list[PlatformRow]:
        return [
            PlatformRow("atomberg", "Atomberg Home", True, [("api_key", "API Key", "Atomberg developer API key", False), ("refresh_token", "Refresh Token", "Atomberg refresh token", True)]),
            PlatformRow("kasa", "TP-Link Kasa", True, [("host", "Device IP / Host", "Optional - leave empty to scan the network", False), ("username", "Username", "Optional cloud username", False), ("password", "Password", "Optional cloud password", True)]),
            PlatformRow("hue", "Philips Hue", True, [("bridge_ip", "Bridge IP Address", "Optional - bridge IP address", False), ("api_key", "API Key / Token", "Optional developer API key", False)]),
            PlatformRow("lg", "LG ThinQ", True, [("username", "Email / Username", "LG ThinQ account email", False), ("password", "Password", "LG ThinQ password", True)]),
            PlatformRow("daikin", "Daikin Smart AC", True, [("ip", "AC IP Address", "Optional local IP of AC unit", False), ("username", "Daikin Username", "Optional cloud account username", False), ("password", "Password", "Optional cloud password", True)]),
            PlatformRow("tuya", "Tuya / Smart Life", True, [("access_id", "Access ID / Client ID", "Tuya IoT platform developer ID", False), ("secret", "Access Secret / Client Secret", "Tuya IoT access secret key", True)]),
            PlatformRow("nest", "Nest / Google Home", True, [("project_id", "Project ID", "Nest device access project ID", False), ("client_secret", "Client Secret", "Nest OAuth client secret", True)]),
            PlatformRow("smartthings", "Samsung SmartThings", True, [("token", "Access Token", "SmartThings personal access token", True)]),
        ]

    def _choose_provider(self, key: str, label: str):
        self._provider_key = key
        self._provider_label = label
        for card in self._platform_buttons:
            is_selected = card.objectName() == f"PlatformCard_{key}"
            if is_selected:
                card.setStyleSheet(f"""
                    QFrame {{
                        background: rgba(255, 179, 0, 0.08);
                        border: 1.5px solid {ACCENT};
                        border-radius: 14px;
                    }}
                """)
            else:
                card.setStyleSheet("""
                    QFrame {
                        background: rgba(255, 255, 255, 0.02);
                        border: 1px solid rgba(255, 255, 255, 0.06);
                        border-radius: 14px;
                    }
                    QFrame:hover {
                        background: rgba(255, 179, 0, 0.04);
                        border: 1px solid rgba(255, 179, 0, 0.3);
                    }
                """)
        self._build_auth_form()
        self._stack.setCurrentIndex(1)
        self._sync_buttons()

    def _build_auth_form(self):
        while self._auth_form.count():
            item = self._auth_form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._fields.clear()
        if not self._provider_key:
            self._auth_desc.setText("Select a platform to build the right authentication form.")
            return
        self._auth_desc.setText(f"Authenticate {self._provider_label}. Credentials are stored locally and encrypted.")
        for key, label, placeholder, secret in next((p.auth_fields for p in self._platforms() if p.key == self._provider_key), []):
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            if secret:
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._fields[key] = edit
            self._auth_form.addRow(label, edit)
        self._account_label = QLineEdit()
        self._account_label.setPlaceholderText("Example: Home, Suryaansh, Bedroom Hub")
        self._auth_form.addRow("Device label", self._account_label)

    def _build_scan_results(self):
        while self._scan_list.count():
            item = self._scan_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._checks.clear()
        if not self._preview:
            self._scan_list.addWidget(QLabel("No devices discovered."))
            self._scan_list.addStretch(1)
            return
        for device in self._preview.get("devices", []):
            box = QCheckBox(f"{device['name']}  •  {device.get('manufacturer', '')}")
            box.setChecked(True)
            box.setStyleSheet(f"QCheckBox {{ color: {TEXT}; padding: 10px; }}")
            self._scan_list.addWidget(box)
            self._checks.append((str(device["external_id"]), box))
        self._scan_list.addStretch(1)

    def _go_next(self):
        idx = self._stack.currentIndex()
        if idx == 0:
            if not self._provider_key:
                return
            self._stack.setCurrentIndex(1)
        elif idx == 1:
            if not self._provider_key:
                return
            credentials = {k: e.text().strip() for k, e in self._fields.items()}
            try:
                self._preview = self._service.preview_discovery(self._provider_key, credentials)
            except Exception as exc:
                self._auth_desc.setText(f"Authentication failed: {exc}")
                return
            self._scan_bar.setValue(55)
            self._scan_label.setText("Discovering devices...")
            self._build_scan_results()
            self._stack.setCurrentIndex(2)
        elif idx == 2:
            selected = [ext_id for ext_id, check in self._checks if check.isChecked()]
            self._result = {
                "provider_key": self._provider_key,
                "account_label": self._account_label.text().strip() or self._provider_label,
                "credentials": {k: e.text().strip() for k, e in self._fields.items()},
                "selected_external_ids": selected,
            }
            self._finish_summary.setText(
                f"{len(selected)} device(s) selected from {self._provider_label}.\nConnected devices are saved locally and will appear under MY DEVICES."
            )
            self._stack.setCurrentIndex(3)
        else:
            self.accept()
        self._sync_buttons()

    def _go_back(self):
        idx = self._stack.currentIndex()
        if idx > 0:
            self._stack.setCurrentIndex(idx - 1)
        self._sync_buttons()

    def _sync_buttons(self):
        idx = self._stack.currentIndex()
        self._back_btn.setEnabled(idx > 0)
        self._next_btn.setText("Connect" if idx == 2 else "Next" if idx < 2 else "Finish")
        self._next_btn.setEnabled(True if idx != 0 else bool(self._provider_key))


class _DeviceTile(ClickableFrame):
    action_requested = pyqtSignal(str, str, dict)
    select_requested = pyqtSignal(str)

    def __init__(self, device: dict[str, Any], parent=None):
        super().__init__(parent)
        self.device = device
        self.setObjectName("DeviceTileFrame")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setMinimumHeight(180)
        self.setMaximumHeight(194)
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        # Header Row (Power Button in top right)
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)
        
        self.power_btn = QPushButton("⏻")
        self.power_btn.setFixedSize(26, 26)
        self.power_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.power_btn.setFont(QFont("Segoe UI", 10))
        
        is_on = bool(device.get("is_on"))
        self.power_btn.clicked.connect(lambda: self.action_requested.emit(str(self.device.get("id", "")), "power", {"is_on": not is_on}))
        header_row.addWidget(self.power_btn)
        lay.addLayout(header_row)
        
        # Product Image Center Container
        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setFixedHeight(58)
        
        kind = str(device.get("device_type", "device")).lower()
        img_path = f"assets/{kind}.jpg"
        from pathlib import Path
        if Path(img_path).exists():
            pix = QPixmap(img_path).scaled(88, 58, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.img_lbl.setPixmap(pix)
        else:
            self.img_lbl.setText(self._glyph(kind))
            self.img_lbl.setFont(QFont("Segoe UI", 18))
            self.img_lbl.setStyleSheet("color: #ffffff;")
        lay.addWidget(self.img_lbl)
        
        # Device details
        self.name_lbl = QLabel(str(device.get("name", "Device")))
        self.name_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet("color: #ffffff;")
        
        self.sub_lbl = QLabel(str(device.get("manufacturer", "")))
        self.sub_lbl.setFont(QFont("Segoe UI", 8))
        self.sub_lbl.setStyleSheet(f"color: {TEXT_DIM};")
        
        lay.addWidget(self.name_lbl)
        lay.addWidget(self.sub_lbl)
        
        # Controls area
        self._control_area = QVBoxLayout()
        self._control_area.setSpacing(3)
        self._control_area.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(self._control_area)
        self._build_controls()
        
        self.set_active(False)

    def _glyph(self, kind: str) -> str:
        return {"fan": "🌀", "light": "💡", "ac": "❄️", "tv": "📺", "plug": "🔌", "sensor": "📡", "curtain": "🪟", "vacuum": "🧹"}.get(kind, "⚙️")

    def _make_slider(self, minv: int, maxv: int, value: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minv, maxv)
        slider.setValue(value)
        slider.setCursor(Qt.CursorShape.SplitHCursor)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: rgba(255, 255, 255, 0.1);
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: #ffb300;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: #ffffff;
                width: 10px;
                height: 10px;
                margin-top: -3px;
                margin-bottom: -3px;
                border-radius: 5px;
            }}
        """)
        return slider

    def _build_controls(self):
        kind = str(self.device.get("device_type", "device")).lower()
        is_on = bool(self.device.get("is_on"))
        traits = self.device.get("traits") if isinstance(self.device.get("traits"), dict) else {}
        
        if kind == "fan":
            current_speed = traits.get("speed", 4)
            try:
                current_speed = int(current_speed)
            except Exception:
                current_speed = 4
                
            self.val_lbl = QLabel(f"Speed {current_speed}" if is_on else "Off")
            self.val_lbl.setFont(QFont("Segoe UI", 8))
            self.val_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
            self._control_area.addWidget(self.val_lbl)
            
            # Segment Speed Indicators
            seg_row = QHBoxLayout()
            seg_row.setSpacing(4)
            seg_row.addStretch(0)
            for s in range(1, 6):
                seg = QFrame()
                seg.setFixedHeight(5)
                seg.setFixedWidth(24)
                if is_on and s <= current_speed:
                    seg.setStyleSheet("background: #ffb300; border-radius: 2.5px;")
                else:
                    seg.setStyleSheet("background: rgba(255, 255, 255, 0.15); border-radius: 2.5px;")
                seg_row.addWidget(seg)
            seg_row.addStretch(1)
            self._control_area.addLayout(seg_row)
            
        elif kind == "light":
            try:
                current_brightness = int(traits.get("brightness", 70))
            except Exception:
                current_brightness = 70
            self.val_lbl = QLabel(f"Brightness {current_brightness}%" if is_on else "Off")
            self.val_lbl.setFont(QFont("Segoe UI", 8))
            self.val_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
            self._control_area.addWidget(self.val_lbl)
            
        elif kind == "tv":
            status_row = QHBoxLayout()
            on_lbl = QLabel("On" if is_on else "Off")
            on_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            on_lbl.setStyleSheet(f"color: {GREEN};" if is_on else f"color: {TEXT_DIM};")
            status_row.addWidget(on_lbl)
            
            if is_on:
                try:
                    current_vol = int(traits.get("volume", 18))
                except Exception:
                    current_vol = 18
                vol_lbl = QLabel(f"Volume {current_vol}")
                vol_lbl.setFont(QFont("Segoe UI", 8))
                vol_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
                status_row.addWidget(vol_lbl)
                status_row.addStretch(1)
                self._control_area.addLayout(status_row)
                
                # Volume track slider
                self.slider = self._make_slider(0, 100, current_vol)
                self.slider.valueChanged.connect(lambda value: self.action_requested.emit(str(self.device.get("id", "")), "volume", {"volume": value}))
                self._control_area.addWidget(self.slider)
            else:
                status_row.addStretch(1)
                self._control_area.addLayout(status_row)
                
        elif kind == "ac":
            try:
                current_temp = int(traits.get("temperature", 24))
            except Exception:
                current_temp = 24
            temp_lbl = QLabel(f"{current_temp}°C" if is_on else "Off")
            temp_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            temp_lbl.setStyleSheet("color: #7bd3f7;" if is_on else f"color: {TEXT_DIM};")
            self._control_area.addWidget(temp_lbl)
            
            if is_on:
                tags_row = QHBoxLayout()
                tags_row.setSpacing(6)
                cool_lbl = QLabel("❄️ Cool")
                cool_lbl.setFont(QFont("Segoe UI", 8))
                cool_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: rgba(255, 255, 255, 0.05); border-radius: 4px; padding: 2px 6px;")
                
                fan_lbl = QLabel("🌀 Fan Auto")
                fan_lbl.setFont(QFont("Segoe UI", 8))
                fan_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: rgba(255, 255, 255, 0.05); border-radius: 4px; padding: 2px 6px;")
                
                tags_row.addWidget(cool_lbl)
                tags_row.addWidget(fan_lbl)
                tags_row.addStretch(1)
                self._control_area.addLayout(tags_row)
                
        elif kind == "plug":
            self.val_lbl = QLabel("On" if is_on else "Off")
            self.val_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            self.val_lbl.setStyleSheet(f"color: {GREEN};" if is_on else f"color: {TEXT_DIM};")
            self._control_area.addWidget(self.val_lbl)
            
        else:
            self._control_area.addWidget(QLabel("No additional controls."))

    def set_active(self, active: bool):
        if active:
            self.setStyleSheet(f"""
                QFrame#DeviceTileFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #12141d, stop:1 #08090e);
                    border: 1.5px solid {ACCENT};
                    border-radius: 18px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#DeviceTileFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f111a, stop:1 #07080b);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 18px;
                }}
                QFrame#DeviceTileFrame:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #141726, stop:1 #0a0b12);
                    border: 1px solid rgba(255, 179, 0, 0.35);
                }}
            """)
            
        is_on = bool(self.device.get("is_on"))
        if is_on:
            self.power_btn.setStyleSheet("QPushButton { color: #37ff5f; background: rgba(55, 255, 95, 0.08); border: 1px solid rgba(55, 255, 95, 0.25); border-radius: 13px; } QPushButton:hover { background: rgba(55, 255, 95, 0.15); }")
        else:
            self.power_btn.setStyleSheet("QPushButton { color: rgba(255, 255, 255, 0.4); background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 13px; } QPushButton:hover { border: 1px solid rgba(255, 255, 255, 0.15); background: rgba(255, 255, 255, 0.06); }")

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            device_id = self.device.get("id")
            if device_id is None:
                return
            self.select_requested.emit(str(device_id))


class BrahmaHomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = SmartHomeService()
        self._selected_device_id: str | None = None
        self._voice_state = "Listening"
        self._voice_phase = 0
        self._drawer_anim = None
        self._device_tiles: list[_DeviceTile] = []
        self._activity_items: list[dict[str, Any]] = []
        self._device_columns_cached = 0

        self.setObjectName("BrahmaHomePageModern")
        self.setStyleSheet(f"QWidget#BrahmaHomePageModern {{ background: transparent; }} QScrollArea {{ background: transparent; border: none; }}")

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        self._main_frame = QFrame()
        self._main_frame.setStyleSheet(
            "QFrame {"
            "background: transparent;"
            "border: none;"
            "}"
        )
        main_lay = QVBoxLayout(self._main_frame)
        main_lay.setContentsMargins(20, 20, 20, 20)
        main_lay.setSpacing(14)
        root.addWidget(self._main_frame, 1)

        self._build_header(main_lay)

        # Split layout for body: Devices (Left) + Recent Activity Feed (Right)
        self._body_layout = QHBoxLayout()
        self._body_layout.setSpacing(16)
        
        # Left side: Devices container
        self._left_container = QWidget()
        self._left_lay = QVBoxLayout(self._left_container)
        self._left_lay.setContentsMargins(0, 0, 0, 0)
        self._left_lay.setSpacing(10)
        self._build_my_devices(self._left_lay)
        self._body_layout.addWidget(self._left_container, 3)
        
        # Recent Activity panel
        self._right_container = QFrame()
        self._right_container.setObjectName("ActivityPanel")
        self._right_container.setStyleSheet(f"""
            QFrame#ActivityPanel {{
                background: rgba(10, 10, 10, 0.4);
                border: 1px solid rgba(255, 179, 0, 0.4);
                border-radius: 16px;
            }}
            QFrame#ActivityPanel:hover {{
                border: 1px solid rgba(255, 179, 0, 0.9);
                background: rgba(255, 179, 0, 0.08);
            }}
        """)
        self._right_lay = QVBoxLayout(self._right_container)
        self._right_lay.setContentsMargins(16, 16, 16, 16)
        self._right_lay.setSpacing(12)
        
        act_title = QLabel("RECENT ACTIVITY")
        act_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        act_title.setStyleSheet(f"color: {TEXT}; letter-spacing: 1px;")
        self._right_lay.addWidget(act_title)
        
        act_scroll = QScrollArea()
        act_scroll.setWidgetResizable(True)
        act_scroll.setFrameShape(QFrame.Shape.NoFrame)
        act_scroll.setStyleSheet("background: transparent; border: none;")
        
        act_host = QWidget()
        act_host.setStyleSheet("background: transparent;")
        self._activity_list = QVBoxLayout(act_host)
        self._activity_list.setContentsMargins(0, 0, 0, 0)
        self._activity_list.setSpacing(8)
        self._activity_list.addStretch(1)
        
        act_scroll.setWidget(act_host)
        self._right_lay.addWidget(act_scroll, 1)
        
        # Link button: View All Activity
        self._view_all_act_btn = QPushButton("View All Activity  >")
        self._view_all_act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_all_act_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {ACCENT}; border: none; font-size: 11px; font-weight: bold; text-align: left; padding-left: 4px; }} QPushButton:hover {{ color: #ff6b6b; }}")
        self._right_lay.addWidget(self._view_all_act_btn)
        
        self._body_layout.addWidget(self._right_container, 1)
        main_lay.addLayout(self._body_layout, 1)

        self._drawer = self._build_drawer()
        self._drawer.hide()

        self._refresh()

    def refresh(self):
        self._refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()

    def _section_card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(_panel_style(32))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        head = QLabel(title)
        head.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        head.setStyleSheet(f"color: {TEXT}; letter-spacing: 1px;")
        lay.addWidget(head)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(255,255,255,0.08);")
        lay.addWidget(line)
        return frame

    def _build_header(self, lay: QVBoxLayout):
        row = QHBoxLayout()
        row.setSpacing(12)
        text = QVBoxLayout()
        title = QLabel("BRAHMA ECHO HOME")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Black))
        title.setStyleSheet(f"color: {TEXT}; letter-spacing: 1px;")
        subtitle = QLabel("Control your smart home with Brahma Echo.")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet(f"color: {TEXT_DIM};")
        text.addWidget(title)
        text.addWidget(subtitle)
        row.addLayout(text, 1)
        self._status_chip = QLabel()
        self._status_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_chip.setStyleSheet(f"QLabel {{ background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 6px 14px; min-width: 110px; }}")
        row.addWidget(self._status_chip)
        self._voice_button = QPushButton("▮▮")
        self._voice_button.setFixedSize(48, 48)
        self._voice_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._voice_button.setStyleSheet(f"QPushButton {{ background: rgba(255, 255, 255, 0.02); color: {TEXT}; border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; font-size: 16px; }} QPushButton:hover {{ border: 1px solid {ACCENT}; background: rgba(255, 179, 0,0.08); }}")
        self._voice_button.clicked.connect(self._toggle_voice_mode)
        row.addWidget(self._voice_button)
        lay.addLayout(row)

    def _build_voice_card(self, lay: QVBoxLayout):
        self._voice_frame = QFrame()
        self._voice_frame.setStyleSheet(_panel_style(36))
        vf = QHBoxLayout(self._voice_frame)
        vf.setContentsMargins(18, 16, 18, 16)
        vf.setSpacing(16)
        self._mic_orb = QLabel("🎤")
        self._mic_orb.setFixedSize(86, 86)
        self._mic_orb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mic_orb.setFont(QFont("Segoe UI", 26))
        self._mic_orb.setStyleSheet(f"QLabel {{ background: rgba(255, 179, 0,0.12); color: {TEXT}; border: 2px solid rgba(255, 179, 0,0.55); border-radius: 43px; }}")
        vf.addWidget(self._mic_orb)
        middle = QVBoxLayout()
        self._voice_state_lbl = QLabel("Listening...")
        self._voice_state_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._voice_state_lbl.setStyleSheet(f"color: {TEXT};")
        self._voice_cmd_lbl = QLabel('"Turn bedroom fan to speed 4"')
        self._voice_cmd_lbl.setStyleSheet(f"color: {TEXT_MED};")
        middle.addWidget(self._voice_state_lbl)
        middle.addWidget(self._voice_cmd_lbl)
        vf.addLayout(middle, 1)
        self._wave = QHBoxLayout()
        self._wave.setSpacing(3)
        self._wave_bars: list[QFrame] = []
        for _ in range(36):
            bar = QFrame()
            bar.setFixedSize(4, 12)
            bar.setStyleSheet("background: rgba(255, 179, 0,0.20); border-radius: 2px;")
            self._wave.addWidget(bar, alignment=Qt.AlignmentFlag.AlignVCenter)
            self._wave_bars.append(bar)
        vf.addLayout(self._wave)
        lay.addWidget(self._voice_frame)

    def _build_my_devices(self, lay: QVBoxLayout):
        header = QHBoxLayout()
        title = QLabel("MY DEVICES")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; letter-spacing: 1px;")
        header.addWidget(title)
        header.addStretch(1)
        self._add_btn = QPushButton("+ Add Device")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setFixedHeight(38)
        self._add_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {TEXT}; border: 1px solid {ACCENT}; border-radius: 12px; padding: 0 14px; }} QPushButton:hover {{ background: rgba(255, 179, 0,0.10); }}")
        self._add_btn.clicked.connect(self._open_add_device)
        header.addWidget(self._add_btn)
        lay.addLayout(header)

        self._empty_state = QFrame()
        self._empty_state.setObjectName("EmptyStateCard")
        self._empty_state.setStyleSheet(f"""
            QFrame#EmptyStateCard {{
                background: rgba(10, 10, 10, 0.4);
                border: 1px solid rgba(255, 179, 0, 0.4);
                border-radius: 16px;
            }}
            QFrame#EmptyStateCard:hover {{
                border: 1px solid rgba(255, 179, 0, 0.9);
                background: rgba(255, 179, 0, 0.08);
            }}
        """)
        empty_lay = QVBoxLayout(self._empty_state)
        empty_lay.setContentsMargins(28, 32, 28, 32)
        empty_lay.setSpacing(10)
        empty_title = QLabel("No devices added.")
        empty_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        empty_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        empty_sub = QLabel("Add a device to start controlling your home.")
        empty_sub.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        empty_lay.addWidget(empty_title, alignment=Qt.AlignmentFlag.AlignHCenter)
        empty_lay.addWidget(empty_sub, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._empty_add_btn = QPushButton("Add Device")
        self._empty_add_btn.setFixedSize(150, 42)
        self._empty_add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._empty_add_btn.setStyleSheet(f"QPushButton {{ background: rgba(255, 179, 0,0.12); color: {TEXT}; border: 1px solid {ACCENT}; border-radius: 12px; }} QPushButton:hover {{ background: rgba(255, 179, 0,0.18); }}")
        self._empty_add_btn.clicked.connect(self._open_add_device)
        empty_lay.addWidget(self._empty_add_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._empty_state)

        self._device_scroll = QScrollArea()
        self._device_scroll.setWidgetResizable(True)
        self._device_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._device_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._device_content = QWidget()
        self._device_content.setStyleSheet("background: transparent;")
        self._device_grid = QGridLayout(self._device_content)
        self._device_grid.setContentsMargins(0, 0, 0, 0)
        self._device_grid.setHorizontalSpacing(12)
        self._device_grid.setVerticalSpacing(12)
        self._device_scroll.setWidget(self._device_content)
        lay.addWidget(self._device_scroll, 1)

    def _build_voice_control_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("VoiceControlCard")
        frame.setStyleSheet(f"""
            QFrame#VoiceControlCard {{
                background: rgba(10, 10, 10, 0.4);
                border: 1px solid rgba(255, 179, 0, 0.4);
                border-radius: 16px;
            }}
            QFrame#VoiceControlCard:hover {{
                border: 1px solid rgba(255, 179, 0, 0.9);
                background: rgba(255, 179, 0, 0.08);
            }}
        """)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        
        left = QVBoxLayout()
        left.setSpacing(6)
        
        title = QLabel("VOICE CONTROL")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; letter-spacing: 1px;")
        left.addWidget(title)
        
        wake_lay = QVBoxLayout()
        wake_lay.setSpacing(2)
        lbl = QLabel("Wake word")
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet(f"color: {TEXT_DIM};")
        
        word = QLabel("Brahma Echo")
        word.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        word.setStyleSheet(f"color: {ACCENT};")
        
        wake_lay.addWidget(lbl)
        wake_lay.addWidget(word)
        left.addLayout(wake_lay)
        lay.addLayout(left, 1)
        
        # Micro wave button on right
        mic_btn = QPushButton("🎙️")
        mic_btn.setFixedSize(38, 38)
        mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mic_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 179, 0,0.08);
                color: {TEXT};
                border: 1px solid rgba(255, 179, 0,0.3);
                border-radius: 19px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: rgba(255, 179, 0,0.18);
                border: 1px solid {ACCENT};
            }}
        """)
        mic_btn.clicked.connect(self._toggle_voice_mode)
        lay.addWidget(mic_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        return frame

    def _build_drawer(self) -> QFrame:
        drawer = QFrame(self)
        drawer.setObjectName("DetailsDrawerFrame")
        drawer.setStyleSheet("""
            QFrame#DetailsDrawerFrame {
                background: rgba(8, 9, 13, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
            }
        """)
        drawer.setGeometry(0, 0, 0, 0)
        lay = QVBoxLayout(drawer)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        
        top = QHBoxLayout()
        title = QLabel("DEVICE DETAILS")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT};")
        top.addWidget(title)
        top.addStretch(1)
        
        close_btn = QPushButton("X")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self._close_drawer)
        close_btn.setStyleSheet(_soft_button_style())
        top.addWidget(close_btn)
        lay.addLayout(top)
        
        card_style = """
            QFrame {
                background: rgba(13, 15, 19, 235);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 14px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """
        
        # 1. Name Card
        self._name_card = QFrame()
        self._name_card.setStyleSheet(card_style)
        nc_lay = QVBoxLayout(self._name_card)
        nc_lay.setContentsMargins(14, 14, 14, 14)
        self._drawer_name = QLabel("")
        self._drawer_name.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._drawer_name.setStyleSheet("color: #ffffff; border: none;")
        nc_lay.addWidget(self._drawer_name)
        lay.addWidget(self._name_card)
        
        # 2. Meta Card
        self._meta_card = QFrame()
        self._meta_card.setStyleSheet(card_style)
        mc_lay = QVBoxLayout(self._meta_card)
        mc_lay.setContentsMargins(14, 14, 14, 14)
        self._drawer_meta = QLabel("")
        self._drawer_meta.setStyleSheet("border: none;")
        mc_lay.addWidget(self._drawer_meta)
        lay.addWidget(self._meta_card)
        
        # 3. State Card
        self._state_card = QFrame()
        self._state_card.setStyleSheet(card_style)
        sc_lay = QVBoxLayout(self._state_card)
        sc_lay.setContentsMargins(14, 14, 14, 14)
        self._drawer_state = QLabel("")
        self._drawer_state.setStyleSheet("border: none;")
        sc_lay.addWidget(self._drawer_state)
        lay.addWidget(self._state_card)
        
        # 4. Info Card
        self._info_card = QFrame()
        self._info_card.setStyleSheet(card_style)
        ic_lay = QVBoxLayout(self._info_card)
        ic_lay.setContentsMargins(14, 14, 14, 14)
        self._drawer_info = QLabel("")
        self._drawer_info.setStyleSheet("border: none;")
        ic_lay.addWidget(self._drawer_info)
        lay.addWidget(self._info_card)
        
        lay.addStretch(1)
        
        self._drawer_actions = QHBoxLayout()
        self._drawer_actions.setSpacing(8)
        lay.addLayout(self._drawer_actions)
        return drawer

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._drawer.isVisible():
            width = min(390, max(330, int(self.width() * 0.28)))
            self._drawer.setGeometry(self.width() - width - 12, 12, width, self.height() - 24)
        self._reflow_devices()
        
        pass

    def _device_columns(self) -> int:
        viewport = self._device_scroll.viewport().width() if hasattr(self, "_device_scroll") else 0
        available = max(1, viewport or self.width())
        if available >= 1240:
            return 4
        if available >= 980:
            return 3
        return 2

    def _reflow_devices(self):
        if not hasattr(self, "_device_grid"):
            return
        columns = self._device_columns()
        if columns == self._device_columns_cached:
            return
        self._device_columns_cached = columns
        self._refresh_devices(self._service.list_devices())

    def _animate_drawer(self, open_: bool):
        if self._drawer_anim and self._drawer_anim.state() == QPropertyAnimation.State.Running:
            self._drawer_anim.stop()
        current = self._drawer.geometry()
        width = min(360, max(300, int(self.width() * 0.28)))
        start = QRect(self.width() - 12, 12, 0, self.height() - 24) if not open_ else current
        end = QRect(self.width() - width - 12, 12, width, self.height() - 24) if open_ else QRect(self.width() - 12, 12, 0, self.height() - 24)
        if open_:
            self._drawer.show()
        self._drawer_anim = QPropertyAnimation(self._drawer, b"geometry", self)
        self._drawer_anim.setDuration(260)
        self._drawer_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._drawer_anim.setStartValue(start)
        self._drawer_anim.setEndValue(end)
        if not open_:
            self._drawer_anim.finished.connect(self._drawer.hide)
        self._drawer_anim.start()

    def _open_drawer(self, device: dict[str, Any]):
        self._selected_device_id = str(device.get("id", ""))
        self._drawer_name.setText(str(device.get("name", "Device")))
        
        self._drawer_meta.setText(f"""
            <div style='line-height: 140%;'>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Manufacturer:</span> <span style='color: #ffffff; font-weight: bold; font-size: 10pt;'>{device.get('manufacturer', '')}</span><br>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Room:</span> <span style='color: #ffffff; font-weight: bold; font-size: 10pt;'>{device.get('room', '')}</span><br>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Connection:</span> <span style='color: #35ff75; font-weight: bold; font-size: 10pt;'>Local</span><br>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Last Updated:</span> <span style='color: rgba(255,255,255,0.7); font-size: 10pt;'>now</span>
            </div>
        """)
        
        traits = device.get("traits") if isinstance(device.get("traits"), dict) else {}
        is_on = bool(device.get("is_on"))
        state_color = "#35ff75" if is_on else "rgba(255,255,255,0.4)"
        self._drawer_state.setText(f"""
            <div style='line-height: 140%;'>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Power:</span> <span style='color: {state_color}; font-weight: bold; font-size: 10pt;'>{'On' if is_on else 'Off'}</span>
            </div>
        """)
        
        self._drawer_info.setText(f"""
            <div style='line-height: 140%;'>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Firmware:</span> <span style='color: #ffffff; font-weight: bold; font-size: 10pt;'>{traits.get('firmware', 'Current')}</span><br>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>MAC:</span> <span style='color: #ffffff; font-weight: bold; font-size: 10pt;'>{traits.get('mac', 'Local')}</span><br>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>IP:</span> <span style='color: #ffffff; font-weight: bold; font-size: 10pt;'>{traits.get('ip', 'Local')}</span><br>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Battery:</span> <span style='color: #ffffff; font-weight: bold; font-size: 10pt;'>{traits.get('battery', 'N/A')}</span><br>
                <span style='color: rgba(255,255,255,0.45); font-size: 10pt;'>Power Consumption:</span> <span style='color: #ffffff; font-weight: bold; font-size: 10pt;'>{traits.get('energy_usage', traits.get('power_usage', 'N/A'))}</span>
            </div>
        """)
        
        while self._drawer_actions.count():
            item = self._drawer_actions.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for text, slot in (("Rename", self._rename_selected), ("Restart", self._restart_selected), ("Forget", self._forget_selected)):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.clicked.connect(slot)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.03);
                    color: {TEXT};
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 179, 0, 0.08);
                    border: 1px solid {ACCENT};
                    color: #ffffff;
                }}
            """)
            self._drawer_actions.addWidget(btn)
        self._animate_drawer(True)

    def _close_drawer(self):
        self._animate_drawer(False)

    def _rename_selected(self):
        if not self._selected_device_id:
            return
        device = self._service.get_device(self._selected_device_id)
        if not device:
            return
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "Rename Device", "New name:", text=str(device.get("name", "")))
        if ok and new_name.strip():
            self._service.rename_device(self._selected_device_id, new_name.strip())
            self._refresh()

    def _restart_selected(self):
        if self._selected_device_id:
            self._service.restart_device(self._selected_device_id)
            self._refresh()

    def _forget_selected(self):
        if self._selected_device_id:
            self._service.forget_device(self._selected_device_id)
            self._selected_device_id = None
            self._close_drawer()
            self._refresh()

    def _refresh(self):
        devices = self._service.list_devices()
        self._refresh_devices(devices)
        self._refresh_activity()
        
        if devices:
            status_html = (
                "<div style='line-height: 1.3;'>"
                "<span style='color: rgba(255,255,255,0.4); font-size: 10px; font-weight: bold;'>SYSTEM</span><br/>"
                "<span style='color: #35ff75; font-size: 12px; font-weight: bold;'>●</span> "
                "<span style='color: #ffffff; font-size: 11px; font-weight: bold;'>Connected</span>"
                "</div>"
            )
        else:
            status_html = (
                "<div style='line-height: 1.3;'>"
                "<span style='color: rgba(255,255,255,0.4); font-size: 10px; font-weight: bold;'>SYSTEM</span><br/>"
                "<span style='color: #ffcc00; font-size: 12px; font-weight: bold;'>●</span> "
                "<span style='color: #ffffff; font-size: 11px; font-weight: bold;'>Ready</span>"
                "</div>"
            )
        self._status_chip.setText(status_html)
        self._empty_state.setVisible(not devices)
        self._device_scroll.setVisible(bool(devices))

    def _refresh_devices(self, devices: list[dict[str, Any]]):
        while self._device_grid.count():
            item = self._device_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._device_tiles.clear()
        
        # Reset row stretches
        for r in range(self._device_grid.rowCount() + 1):
            self._device_grid.setRowStretch(r, 0)
            
        if not devices:
            return
        columns = self._device_columns()
        self._device_columns_cached = columns
        for idx, device in enumerate(devices):
            tile = _DeviceTile(device)
            tile.select_requested.connect(self._on_tile_selected)
            tile.action_requested.connect(self._on_device_action)
            tile.set_active(str(device.get("id")) == self._selected_device_id)
            self._device_grid.addWidget(tile, idx // columns, idx % columns)
            self._device_tiles.append(tile)
            
        # Add stretch on the last row to absorb extra vertical space
        last_row = (len(devices) - 1) // columns + 1
        self._device_grid.setRowStretch(last_row, 1)

    def _refresh_activity(self):
        while self._activity_list.count():
            item = self._activity_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._activity_items = self._service.recent_activity(10)
        if not self._activity_items:
            empty = QLabel("No recent activity yet.")
            empty.setStyleSheet(f"color: {TEXT_DIM};")
            self._activity_list.addWidget(empty)
            self._activity_list.addStretch(1)
            return
            
        for row in self._activity_items:
            item = QFrame()
            item.setStyleSheet("QFrame { background: transparent; border: none; }")
            box = QHBoxLayout(item)
            box.setContentsMargins(4, 4, 4, 4)
            box.setSpacing(12)
            
            # Timestamp (e.g. 12:08 PM)
            time_str = QDateTime.fromMSecsSinceEpoch(int(row["created_at"])).toString("h:mm AP")
            time_lbl = QLabel(time_str)
            time_lbl.setFont(QFont("Segoe UI", 9))
            time_lbl.setStyleSheet(f"color: {TEXT_DIM}; min-width: 60px;")
            box.addWidget(time_lbl)
            
            # Icon Badge
            kind = str(row.get("device_type", "device")).lower()
            badge = QLabel(self._activity_glyph(kind))
            badge.setFixedSize(32, 32)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFont(QFont("Segoe UI", 11))
            
            badge_style = {
                "fan": "background: rgba(53, 255, 117, 0.08); color: #35ff75; border: 1px solid rgba(53, 255, 117, 0.25); border-radius: 16px;",
                "light": "background: rgba(255, 165, 0, 0.08); color: #ffa500; border: 1px solid rgba(255, 165, 0, 0.25); border-radius: 16px;",
                "ac": "background: rgba(123, 211, 247, 0.08); color: #7bd3f7; border: 1px solid rgba(123, 211, 247, 0.25); border-radius: 16px;",
                "tv": "background: rgba(0, 180, 216, 0.08); color: #00b4d8; border: 1px solid rgba(0, 180, 216, 0.25); border-radius: 16px;",
                "plug": "background: rgba(255, 255, 255, 0.05); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 16px;",
            }.get(kind, "background: rgba(255, 255, 255, 0.05); color: #ffffff; border-radius: 16px;")
            badge.setStyleSheet(badge_style)
            box.addWidget(badge)
            
            # Details Text
            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            title = QLabel(str(row["title"]))
            title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            title.setStyleSheet("color: #ffffff;")
            
            detail = QLabel(str(row["detail"]))
            detail.setFont(QFont("Segoe UI", 9))
            detail.setStyleSheet(f"color: {TEXT_DIM};")
            text_box.addWidget(title)
            text_box.addWidget(detail)
            
            box.addLayout(text_box, 1)
            self._activity_list.addWidget(item)
            
        self._activity_list.addStretch(1)

    def _activity_glyph(self, kind: str) -> str:
        return {"fan": "🌀", "light": "💡", "ac": "❄️", "tv": "📺", "plug": "🔌"}.get(kind, "⚙️")

    def _on_tile_selected(self, device_id: str):
        device = self._service.get_device(device_id)
        if not device:
            return
        self._selected_device_id = device_id
        for tile in self._device_tiles:
            tile.set_active(str(tile.device.get("id")) == device_id)
        self._open_drawer(device)

    def _on_device_action(self, device_id: str, action: str, payload: dict):
        try:
            self._service.execute_device_action(device_id, action, payload)
        except Exception:
            return
        self._refresh()
        device = self._service.get_device(device_id)
        if device:
            self._open_drawer(device)

    def _toggle_voice_mode(self):
        states = ["Idle", "Listening", "Thinking", "Executing", "Completed"]
        self._voice_phase = (self._voice_phase + 1) % len(states)
        self._voice_state = states[self._voice_phase]
        # Some UI paths may call this before voice widgets are built; guard access.
        if hasattr(self, "_voice_state_lbl") and isinstance(getattr(self, "_voice_state_lbl"), QLabel):
            try:
                self._voice_state_lbl.setText(f"{self._voice_state}...")
            except Exception:
                pass
        if hasattr(self, "_voice_state_small") and isinstance(getattr(self, "_voice_state_small"), QLabel):
            try:
                self._voice_state_small.setText(self._voice_state)
            except Exception:
                pass

    def _animate_voice(self):
        self._voice_phase += 1
        if hasattr(self, "_wave_bars") and self._wave_bars:
            for idx, bar in enumerate(self._wave_bars):
                height = 8 + int(18 * abs(((self._voice_phase + idx) % 14) - 7) / 7)
                bar.setFixedHeight(max(8, min(40, height)))
                bar.setStyleSheet(f"background: {'rgba(255, 179, 0,0.55)' if self._voice_state in ('Listening', 'Executing') else 'rgba(255,255,255,0.18)'}; border-radius: 2px;")
        if hasattr(self, "_voice_small_bars") and self._voice_small_bars:
            for idx, bar in enumerate(self._voice_small_bars):
                height = 6 + int(10 * abs(((self._voice_phase + idx) % 10) - 5) / 5)
                bar.setFixedHeight(max(6, min(24, height)))
                bar.setStyleSheet(f"background: {'rgba(255, 179, 0,0.35)' if self._voice_state in ('Listening', 'Executing') else 'rgba(255,255,255,0.15)'}; border-radius: 2px;")
        if hasattr(self, "_voice_cmd_lbl") and self._voice_cmd_lbl:
            self._voice_cmd_lbl.setText({"Idle": '"Brahma Echo"', "Listening": '"Turn bedroom fan to speed 4"', "Thinking": '"Understanding..."', "Executing": '"Applying command..."', "Completed": '"Done"'}.get(self._voice_state, '"Brahma Echo"'))
        if hasattr(self, "_mic_orb") and self._mic_orb:
            self._mic_orb.setText("🎙️" if self._voice_state in ("Listening", "Executing") else "🎙️")

    def _open_add_device(self):
        dialog = AddDeviceDialog(self._service, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dialog.result_payload()
        provider_key = str(payload.get("provider_key", ""))
        selected = list(payload.get("selected_external_ids", []))
        if not provider_key or not selected:
            return
        creds = dict(payload.get("credentials", {}))
        label = str(payload.get("account_label", "Home"))
        try:
            self._service.connect_devices(provider_key, label, creds, selected)
        except Exception:
            return
        self._refresh()
