from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


def apply_app_style(app: QApplication) -> None:
    app.setStyle("Fusion")

    font = QFont()
    font.setFamilies(["Pretendard", "Inter", "Noto Sans CJK KR", "Arial"])
    font.setPointSize(10)
    app.setFont(font)

    app.setStyleSheet("""
/* ------------------------------------------------------------------
   Base
------------------------------------------------------------------ */
QWidget {
    color: #1c1c1e;
    font-size: 13px;
}

QMainWindow#AppWindow,
QWidget#Root {
    background: #ffffff;
}

QStackedWidget#MainStack {
    background: #ffffff;
}

/* ------------------------------------------------------------------
   Sidebar
------------------------------------------------------------------ */
QFrame#Sidebar {
    background: rgba(246, 246, 248, 235);
    border-right: 1px solid rgba(0, 0, 0, 22);
}

QLabel#AppTitle {
    padding: 2px 4px 8px 4px;
    color: rgba(0, 0, 0, 170);
    font-size: 14px;
    font-weight: 800;
}

QLabel#SidebarSection {
    padding: 10px 4px 2px 4px;
    color: rgba(0, 0, 0, 120);
    font-size: 11px;
    font-weight: 800;
}

QPushButton#SidebarTab {
    min-height: 31px;
    padding: 5px 9px;
    border: 0;
    border-radius: 7px;
    background: transparent;
    color: rgba(0, 0, 0, 185);
    text-align: left;
    font-weight: 600;
}

QPushButton#SidebarTab:hover {
    background: rgba(0, 0, 0, 12);
}

QPushButton#SidebarTab:checked {
    background: #007aff;
    color: #ffffff;
}

/* ------------------------------------------------------------------
   Sidebar source card
------------------------------------------------------------------ */
QFrame#SourceCard {
    background: rgba(255, 255, 255, 170);
    border: 1px solid rgba(0, 0, 0, 22);
    border-radius: 11px;
}

QLabel#StatusDotIdle {
    background: rgba(0, 0, 0, 70);
    border-radius: 3px;
}

QLabel#StatusDotOk {
    background: #30d158;
    border-radius: 3px;
}

QLabel#SourceCardTitle {
    color: rgba(0, 0, 0, 120);
    font-size: 10px;
    font-weight: 800;
}

QLabel#SourceState {
    color: rgba(0, 0, 0, 125);
    font-size: 10px;
    font-weight: 700;
}

QLabel#SourceName {
    color: #1c1c1e;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 700;
}

QLabel#SourceMeta {
    color: rgba(0, 0, 0, 120);
    font-size: 10px;
}

QPushButton#SourceOpenButton {
    min-height: 24px;
    padding: 3px 10px;
    border-radius: 6px;
    border: 1px solid rgba(0, 0, 0, 28);
    background: rgba(255, 255, 255, 210);
    color: #007aff;
    font-weight: 700;
}

QPushButton#SourceOpenButton:disabled {
    color: rgba(0, 0, 0, 80);
}

/* ------------------------------------------------------------------
   Sensor header
------------------------------------------------------------------ */
QFrame#SensorHeader {
    background: #ffffff;
    border-bottom: 1px solid rgba(0, 0, 0, 18);
}

QLabel#SensorIcon {
    background: rgba(0, 122, 255, 18);
    color: #007aff;
    border-radius: 13px;
    font-size: 20px;
    font-weight: 900;
}

QLabel#PageTitle {
    color: #000000;
    font-size: 31px;
    font-weight: 900;
}

QLabel#PageTitleEn {
    color: rgba(0, 0, 0, 90);
    font-size: 13px;
    font-weight: 700;
}

QLabel#PageDescription {
    color: rgba(0, 0, 0, 155);
    font-size: 13px;
}

QLabel#ConversionCount {
    color: rgba(0, 0, 0, 120);
    font-size: 11px;
    font-weight: 800;
}

QLabel#SmallSectionTitle {
    color: rgba(0, 0, 0, 90);
    font-size: 10px;
    font-weight: 800;
}

QLabel#TopicChip {
    color: rgba(0, 0, 0, 145);
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 10.5px;
}

/* ------------------------------------------------------------------
   Mode segmented bar
------------------------------------------------------------------ */
QFrame#ModeSection {
    background: #f9f9fb;
    border-bottom: 1px solid rgba(0, 0, 0, 18);
}

QFrame#ModeBar {
    background: rgba(0, 0, 0, 18);
    border-radius: 8px;
    min-height: 32px;
    max-height: 32px;
}

QPushButton#ModeTab {
    min-height: 26px;
    max-height: 26px;
    padding: 0 13px;
    border-radius: 6px;
    border: 0;
    background: transparent;
    color: rgba(0, 0, 0, 150);
    font-size: 12px;
    font-weight: 700;
}

QPushButton#ModeTab:hover {
    color: #000000;
}

QPushButton#ModeTab:checked {
    background: #ffffff;
    color: #007aff;
    border: 1px solid rgba(0, 0, 0, 18);
}

/* ------------------------------------------------------------------
   Body layout
------------------------------------------------------------------ */
QFrame#PageBody {
    background: #ffffff;
}

QFrame#SettingsCard,
QFrame#SummaryCard {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 22);
    border-radius: 14px;
}

QLabel#CardTitle {
    color: rgba(0, 0, 0, 155);
    font-size: 12px;
    font-weight: 900;
}

QScrollArea#SettingsScroll {
    background: transparent;
    border: 0;
}

QScrollArea#SummaryScroll {
    background: transparent;
    border: none;
}

QScrollArea#SummaryScroll > QWidget > QWidget {
    background: transparent;
}
                      
QWidget#SettingsForm {
    background: transparent;
}

QFrame#FieldRow {
    background: transparent;
}

QLabel#FieldLabelKo {
    color: #1c1c1e;
    font-size: 12.5px;
    font-weight: 700;
}

QLabel#FieldLabelEn {
    color: rgba(0, 0, 0, 85);
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 9.5px;
    font-weight: 600;
}

                      /* ------------------------------------------------------------------
   Choice chips
------------------------------------------------------------------ */
QFrame#ChoiceBar {
    background: rgba(0, 0, 0, 18);
    border-radius: 7px;
}

QPushButton#ChoiceChip {
    min-height: 24px;
    padding: 3px 11px;
    border-radius: 5px;
    border: 0;
    background: transparent;
    color: rgba(0, 0, 0, 150);
    font-size: 11.5px;
    font-weight: 800;
}

QPushButton#ChoiceChip:hover {
    color: #000000;
    background: rgba(255, 255, 255, 90);
}

QPushButton#ChoiceChip:checked {
    background: #ffffff;
    color: #007aff;
    border: 1px solid rgba(0, 0, 0, 18);
}

QPushButton#ChoiceChip:disabled {
    color: rgba(0, 0, 0, 110);
    background: rgba(255, 255, 255, 130);
}
                      
/* ------------------------------------------------------------------
   Inputs
------------------------------------------------------------------ */
QLineEdit,
QTextEdit,
QPlainTextEdit,
QSpinBox,
QDoubleSpinBox,
QComboBox {
    min-height: 25px;
    padding: 3px 8px;
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 36);
    border-radius: 6px;
    selection-background-color: rgba(0, 122, 255, 75);
}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus,
QComboBox:focus {
    border: 1px solid #007aff;
}

QComboBox {
    padding-right: 22px;
    background: #ffffff;
}

QComboBox::drop-down {
    width: 22px;
    border: 0;
}

QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 40);
    selection-background-color: #007aff;
    selection-color: white;
}

QFrame#InputGroup {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 36);
    border-radius: 6px;
}

QFrame#InputGroup QLineEdit {
    border: 0;
    background: transparent;
}

QPushButton#BrowseButton {
    min-width: 70px;
    min-height: 25px;
    padding: 2px 10px;
    border: 0;
    border-left: 1px solid rgba(0, 0, 0, 30);
    border-radius: 0;
    background: transparent;
    color: #007aff;
    font-size: 11.5px;
    font-weight: 800;
}

QPushButton#BrowseButton:hover {
    background: rgba(0, 0, 0, 8);
}

/* ------------------------------------------------------------------
   Buttons
------------------------------------------------------------------ */
QPushButton {
    min-height: 28px;
    padding: 5px 12px;
    border-radius: 7px;
    border: 1px solid rgba(0, 0, 0, 35);
    background: #ffffff;
    color: #1c1c1e;
    font-weight: 700;
}

QPushButton:hover {
    background: #f3f3f5;
}

QPushButton:pressed {
    background: #e8e8ec;
}

QPushButton#PrimaryButton {
    min-height: 36px;
    background: #007aff;
    color: #ffffff;
    border: 0;
    border-radius: 10px;
    font-weight: 900;
}

QPushButton#PrimaryButton:hover {
    background: #1588ff;
}

QPushButton#PrimaryButton:disabled {
    background: rgba(0, 122, 255, 90);
    color: rgba(255, 255, 255, 190);
}

/* ------------------------------------------------------------------
   Summary
------------------------------------------------------------------ */
QWidget#SummaryPanelContent {
    background: transparent;
}

QLabel#SummaryTitle {
    color: #1c1c1e;
    font-size: 13px;
    font-weight: 900;
}

QFrame#SummaryItem {
    background: #f9f9fb;
    border: 1px solid rgba(0, 0, 0, 18);
    border-radius: 9px;
}

QLabel#SummaryKey {
    color: rgba(0, 0, 0, 95);
    font-size: 10px;
    font-weight: 800;
}

QLabel#SummaryValue {
    color: rgba(0, 0, 0, 170);
    font-size: 11.5px;
    font-weight: 600;
}

/* ------------------------------------------------------------------
   Log
------------------------------------------------------------------ */
QFrame#LogSection {
    background: #ffffff;
}

QLabel#LogTitle {
    color: rgba(0, 0, 0, 130);
    font-size: 11px;
    font-weight: 900;
}

QTextEdit#LogView,
QPlainTextEdit#LogView {
    background: #1c1c1e;
    color: rgba(255, 255, 255, 215);
    border: 0;
    border-radius: 12px;
    padding: 10px;
    font-family: "JetBrains Mono", "SF Mono", "Consolas", monospace;
    font-size: 12px;
}

/* ------------------------------------------------------------------
   Scroll
------------------------------------------------------------------ */
QScrollBar:vertical {
    width: 12px;
    background: transparent;
}

QScrollBar::handle:vertical {
    min-height: 26px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 45);
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QCheckBox {
    spacing: 8px;
    font-weight: 600;
}
""")