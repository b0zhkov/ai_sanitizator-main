import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox,
    QStackedWidget, QInputDialog, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QAction

import document_loading
import strip_inv_chars
import normalizator

class SanitizationApp(QMainWindow):
    """
    Main application window for the Text Sanitization Tool.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Sanitizer Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        self.raw_text: str = ""
        self.clean_text: str = ""

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        self.header_label = QLabel("Text Sanitizer Tool")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.main_layout.addWidget(self.header_label)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self._init_input_page()
        self._init_preview_page()
        self._init_result_page()

        self.stack.setCurrentIndex(0)

    def _init_input_page(self):
        """Page 1: Input Selection (Import or Paste)"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)

        lbl_instruction = QLabel("Select how you would like to input your text:")
        lbl_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_instruction.setFont(QFont("Arial", 14))
        
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(20)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_import = self._create_styled_button("Import File", self._handle_import, "background-color: #3498db; color: white;")
        
        btn_paste = self._create_styled_button("Paste Text", self._handle_paste, "background-color: #2ecc71; color: white;")

        btn_layout.addWidget(btn_import)
        btn_layout.addWidget(btn_paste)

        layout.addWidget(lbl_instruction)
        layout.addWidget(btn_container)
        
        self.page_input = page
        self.stack.addWidget(page)

    def _init_preview_page(self):
        """Page 2: Preview Loaded Text"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        lbl_header = QLabel("Preview Loaded Text")
        lbl_header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlaceholderText("No text loaded...")
        
        btn_layout = QHBoxLayout()
        btn_back = self._create_styled_button("Back", self._go_to_input, "background-color: #95a5a6; color: white;", width=120)
        btn_clean = self._create_styled_button("Clean Text", self._handle_clean, "background-color: #e74c3c; color: white;", width=150)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_back)
        btn_layout.addWidget(btn_clean)
        
        layout.addWidget(lbl_header)
        layout.addWidget(self.preview_edit)
        layout.addLayout(btn_layout)

        self.page_preview = page
        self.stack.addWidget(page)

    def _init_result_page(self):
        """Page 3: Side-by-Side Comparison"""
        page = QWidget()
        layout = QVBoxLayout(page)

        lbl_header = QLabel("Sanitization Results: Before vs After")
        lbl_header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.before_edit = self._create_labeled_textarea("Original Text")
        self.after_edit = self._create_labeled_textarea("Cleaned Text")
        
        splitter.addWidget(self.before_edit['container'])
        splitter.addWidget(self.after_edit['container'])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        action_layout = QHBoxLayout()
        btn_copy = self._create_styled_button("Copy", self._handle_copy, "background-color: #2ecc71; color: white;")
        btn_new = self._create_styled_button("New Clean", self._handle_restart, "background-color: #3498db; color: white;")
        btn_close = self._create_styled_button("Close", self.close, "background-color: #7f8c8d; color: white;")
        
        action_layout.addStretch()
        action_layout.addWidget(btn_copy)
        action_layout.addWidget(btn_new)
        action_layout.addWidget(btn_close)
        action_layout.addStretch()

        layout.addWidget(lbl_header)
        layout.addWidget(splitter)
        layout.addLayout(action_layout)

        self.page_result = page
        self.stack.addWidget(page)

    def _create_styled_button(self, text: str, callback, style: str, width: int = 180, height: int = 50) -> QPushButton:
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        btn.setFixedSize(width, height)
        btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                {style}
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        return btn

    def _create_labeled_textarea(self, label_text: str) -> dict:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 12))
        text_edit.setMinimumHeight(400)
        
        layout.addWidget(label)
        layout.addWidget(text_edit)
        
        return {'container': container, 'text_edit': text_edit}

    def _handle_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Supported Files (*.txt *.docx *.html *.pdf);;All Files (*)"
        )
        if file_path:
            try:
                content = document_loading.load_file_content(file_path)
                self._load_and_show_preview(content)
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to load file:\n{str(e)}")

    def _handle_paste(self):
        text, ok = QInputDialog.getMultiLineText(
            self, "Paste Text", "Paste your text below:"
        )
        if ok and text:
            self._load_and_show_preview(text)

    def _load_and_show_preview(self, text: str):
        if not text:
            QMessageBox.warning(self, "Empty Content", "The imported text is empty.")
            return

        self.raw_text = text
        self.preview_edit.setText(text)
        self.stack.setCurrentIndex(1)

    def _go_to_input(self):
        self.stack.setCurrentIndex(0)
        self.raw_text = ""
        self.preview_edit.clear()

    def _handle_clean(self):
        if not self.raw_text:
            return

        try:
            sanitized = strip_inv_chars.sanitize_text(self.raw_text)
            self.clean_text = normalizator.normalize_punctuation(sanitized)
            
            self.before_edit['text_edit'].setText(self.raw_text)
            self.after_edit['text_edit'].setText(self.clean_text)
            
            self.stack.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, "Cleaning Error", f"An error occurred during sanitization:\n{str(e)}")


    def _handle_copy(self):
        if not self.clean_text:
            QMessageBox.warning(self, "No Text", "There is no cleaned text to copy.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.clean_text)
        QMessageBox.information(self, "Success", "Cleaned text copied to clipboard!")

    def _handle_restart(self):
        self.raw_text = ""
        self.clean_text = ""
        self.preview_edit.clear()
        self.before_edit['text_edit'].clear()
        self.after_edit['text_edit'].clear()
        self.stack.setCurrentIndex(0)

def main():
    app = QApplication(sys.argv)
    
    app.setStyle("Breeze")
    
    window = SanitizationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()