desc = "ChromaticBrowser; a colorful chromium-based web browser built using PyQt6 and QWebEngine. you dont need to install those the script will automatically do that"

print(desc)
# ok, start running the actual browser now
total_hours_wasted_here = 134
import sys
import os
import json
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QPushButton, QListWidget, QDialog,
    QLabel, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineDownloadRequest

APP_NAME = "ChromaticBrowser"
HOME_URL = "https://www.google.com"
BOOKMARKS_FILE = "bookmarks.json"

# Ensure bookmarks file exists
if not os.path.exists(BOOKMARKS_FILE):
    with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)


def load_bookmarks():
    try:
        with open(BOOKMARKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_bookmarks(bookmarks):
    with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(bookmarks, f, indent=2)


class BrowserTab(QWidget):
    def __init__(self, parent=None, url=HOME_URL):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl(url))
        self.layout.addWidget(self.webview)
        self.setLayout(self.layout)


class DownloadsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloads")
        self.resize(500, 300)
        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

    def add_download(self, filename, state, path=None):
        text = f"{filename} — {state}"
        if path:
            text += f" — {path}"
        self.list_widget.addItem(text)


class BookmarkManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.resize(400, 400)
        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.open_btn = QPushButton("Open")
        self.delete_btn = QPushButton("Delete")
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.delete_btn)
        self.layout.addLayout(btn_layout)

        self.open_btn.clicked.connect(self.open_selected)
        self.delete_btn.clicked.connect(self.delete_selected)

        self._load()

    def _load(self):
        self.bookmarks = load_bookmarks()
        self.list_widget.clear()
        for bm in self.bookmarks:
            self.list_widget.addItem(f"{bm.get('title','(no title)')} — {bm.get('url')}")

    def open_selected(self):
        idx = self.list_widget.currentRow()
        if idx >= 0:
            url = self.bookmarks[idx]['url']
            self.accept()
            self.selected_url = url
        else:
            QMessageBox.information(self, "Select", "Please select a bookmark to open")

    def delete_selected(self):
        idx = self.list_widget.currentRow()
        if idx >= 0:
            confirm = QMessageBox.question(self, "Delete", "Delete selected bookmark?")
            if confirm == QMessageBox.StandardButton.Yes:
                del self.bookmarks[idx]
                save_bookmarks(self.bookmarks)
                self._load()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self.on_download_requested)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_urlbar_from_tab)
        self.setCentralWidget(self.tabs)

        # Create downloads dialog first
        self.downloads_dialog = DownloadsDialog(self)

        # Initialize theme
        self.dark_mode = False

        # Toolbar
        self._create_toolbar()
        self.status = self.statusBar()

        # Apply initial theme
        self.apply_light_theme()

        # Home tab
        self.add_tab(HOME_URL, label='Home')

        # Bookmarks
        self.bookmarks = load_bookmarks()

        # Active downloads list
        self.active_downloads = []

    # ---------- THEMES ----------
    def apply_light_theme(self):
        self.setStyleSheet('''
            QMainWindow {
                background: qlineargradient(x1:0 y1:0, x2:1 y2:1,
                                            stop:0 #ff9a9e, stop:0.5 #fad0c4, stop:1 #fad0c4);
                color: #222;
            }
            QToolBar {
                background: rgba(255,255,255,0.9);
                border-radius: 10px;
                padding: 6px;
            }
            QLineEdit {
                padding: 6px;
                border-radius: 6px;
                background: white;
                color: #222;
            }
            QPushButton {
                border-radius: 8px;
                padding: 6px;
                background: #fdfdfd;
                color: #222;
            }
            QTabWidget::pane { background: white; }
        ''')

    def apply_dark_theme(self):
        self.setStyleSheet('''
            QMainWindow {
                background-color: #121212;
                color: #e0e0e0;
            }
            QToolBar {
                background: #1f1f1f;
                border-bottom: 1px solid #333;
                padding: 6px;
            }
            QLineEdit {
                background: #2a2a2a;
                color: #f0f0f0;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton {
                background: #2a2a2a;
                color: #f0f0f0;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 6px;
            }
            QPushButton:hover {
                background: #333;
            }
            QTabWidget::pane { background: #1a1a1a; }
            QListWidget { background: #1c1c1c; color: #f0f0f0; }
        ''')

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.apply_dark_theme()
            self.darkmode_action.setText("☀️")
            self.status.showMessage("Dark mode enabled")
        else:
            self.apply_light_theme()
            self.darkmode_action.setText("🌙")
            self.status.showMessage("Light mode enabled")

    # ---------- UI ----------
    def _create_toolbar(self):
        self.toolbar = QToolBar("Navigation")
        self.addToolBar(self.toolbar)

        # Navigation
        back_btn = QAction("←", self)
        back_btn.triggered.connect(lambda: self.current_webview().back())
        self.toolbar.addAction(back_btn)

        forward_btn = QAction("→", self)
        forward_btn.triggered.connect(lambda: self.current_webview().forward())
        self.toolbar.addAction(forward_btn)

        reload_btn = QAction("⟳", self)
        reload_btn.triggered.connect(lambda: self.current_webview().reload())
        self.toolbar.addAction(reload_btn)

        home_btn = QAction("🏠", self)
        home_btn.triggered.connect(lambda: self.current_webview().setUrl(QUrl(HOME_URL)))
        self.toolbar.addAction(home_btn)

        newtab_btn = QAction("➕", self)
        newtab_btn.triggered.connect(lambda: self.add_tab(HOME_URL, "New Tab"))
        self.toolbar.addAction(newtab_btn)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.urlbar)

        bm_btn = QAction("★", self)
        bm_btn.triggered.connect(self.open_bookmarks_manager)
        self.toolbar.addAction(bm_btn)

        downloads_btn = QAction("⬇", self)
        downloads_btn.triggered.connect(self.downloads_dialog.show)
        self.toolbar.addAction(downloads_btn)

        # 🌙 Dark mode toggle
        self.darkmode_action = QAction("🌙", self)
        self.darkmode_action.triggered.connect(self.toggle_dark_mode)
        self.toolbar.addAction(self.darkmode_action)

    def add_tab(self, url, label="New Tab"):
        new_tab = BrowserTab(self, url)
        self.tabs.addTab(new_tab, label)
        self.tabs.setCurrentWidget(new_tab)
        new_tab.webview.urlChanged.connect(lambda _: self.update_urlbar_from_tab(self.tabs.currentIndex()))

    def current_webview(self):
        tab = self.tabs.currentWidget()
        if isinstance(tab, BrowserTab):
            return tab.webview
        return None

    def close_tab(self, index):
        self.tabs.removeTab(index)

    def update_urlbar_from_tab(self, index):
        tab = self.tabs.widget(index)
        if tab:
            self.urlbar.setText(tab.webview.url().toString())

    def navigate_to_url(self):
        url = self.urlbar.text()
        if not url.startswith("http"):
            url = "https://" + url
        tab = self.current_webview()
        if tab:
            tab.setUrl(QUrl(url))

    # ---------- DOWNLOADS ----------
    def on_download_requested(self, download: QWebEngineDownloadRequest):
        suggested = download.downloadFileName()
        path, _ = QFileDialog.getSaveFileName(self, "Save File", suggested)
        if not path:
            download.cancel()
            return

        download.setPath(path)
        download.accept()

        # Keep alive to prevent crashes
        self.active_downloads.append(download)

        download.downloadProgress.connect(
            lambda received, total, d=download: self.on_download_progress(d, received, total)
        )
        download.finished.connect(lambda d=download: self.on_download_finished(d))

        self.downloads_dialog.add_download(suggested, "downloading...", path)

    def on_download_progress(self, download, received, total):
        filename = os.path.basename(download.path())
        percent = int(received / total * 100) if total > 0 else 0
        self.status.showMessage(f"Downloading {filename}... {percent}%")

    def on_download_finished(self, download):
        filename = os.path.basename(download.path())
        if download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            self.downloads_dialog.add_download(filename, "✅ completed", download.path())
            self.status.showMessage(f"Download completed: {filename}")
        else:
            self.downloads_dialog.add_download(filename, "❌ failed", download.path())
            self.status.showMessage(f"Download failed: {filename}")

        try:
            self.active_downloads.remove(download)
        except ValueError:
            pass

    def open_bookmarks_manager(self):
        dlg = BookmarkManagerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            url = getattr(dlg, 'selected_url', None)
            if url:
                self.add_tab(url)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
