import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'changes-log'))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'text-analysis')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'text-rewriting')))
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox,
    QStackedWidget, QInputDialog, QSplitter, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QSize, QThread, QObject, QPropertyAnimation, QEasingCurve,pyqtSignal
from PyQt6.QtGui import QFont, QAction, QIcon
import document_loading
import strip_inv_chars
import normalizator
from changes_log import build_changes_log, Change
import llm_validator
from rewriting_agent import rewriting_agent

class Worker(QObject):
    finished = pyqtSignal(str, list, float)
    error = pyqtSignal(str)
    progress_chunk = pyqtSignal(str)

    def __init__(self, raw_text):
        super().__init__()
        self.raw_text = raw_text

    def run(self):
        try:
            # 1. Sanitize
            sanitized_text, changes = build_changes_log(self.raw_text)
            
            # 2. Analyze
            analysis = llm_validator.validate_text(sanitized_text)
            if "error" in analysis:
                raise Exception(f"Analysis failed: {analysis['error']}")
                
            # 3. Rewrite (with Streaming)
            rewritten_text_chunks = []
            for chunk in rewriting_agent.stream_rewrite(sanitized_text, analysis):
                self.progress_chunk.emit(chunk)
                rewritten_text_chunks.append(chunk)

            rewritten_text = "".join(rewritten_text_chunks)
            
            # Add rewriting entry to log
            changes.append(Change(
                description="Applied AI Rewriting (Clean + Rewrite)",
                text_before=sanitized_text,
                text_after=rewritten_text
            ))
            
            llm_critique = analysis.get("llm_critique", {})
            ai_score = llm_critique.get("ai_score", 0.0)

            self.finished.emit(rewritten_text, changes, ai_score)
        except Exception as e:
            self.error.emit(str(e))

class SanitizationApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Sanitizer and Rewriter")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        self.raw_text: str = ""
        self.clean_text: str = ""
        self.change_log: list = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        self.header_label = QLabel("Text Sanitizer")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_font = QFont("Roboto", 28)
        header_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 8)
        self.header_label.setFont(header_font)
        self.main_layout.addWidget(self.header_label)

        self.opacity_effect = QGraphicsOpacityEffect(self.header_label)
        self.header_label.setGraphicsEffect(self.opacity_effect)
        
        self.opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_animation.setDuration(1500)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self._init_input_page()
        self._init_preview_page()
        self._init_result_page()

        self.stack.setCurrentIndex(0)

    def _init_input_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)

        lbl_instruction = QLabel("Select how you would like to input your text:")
        lbl_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_instruction.setFont(QFont("Helvetica", 16))

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(20)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        import_icon = QIcon("assets/folder-plus-circle.png")
        paste_icon = QIcon("assets/clipboard.png")

        btn_import = self._create_styled_button("   Import File", self._handle_import, "background-color: #3498db; color: white; text-align: left; padding-left: 20px;")
        
        btn_paste = self._create_styled_button("   Paste Text", self._handle_paste, "background-color: #2ecc71; color: white; text-align: left; padding-left: 20px;")
        
        btn_import.setIcon(import_icon)
        btn_import.setIconSize(QSize(24, 24))

        btn_paste.setIcon(paste_icon)
        btn_paste.setIconSize(QSize(24, 24))

        btn_layout.addWidget(btn_import)
        btn_layout.addWidget(btn_paste)

        layout.addWidget(lbl_instruction)
        layout.addWidget(btn_container)
        
        self.page_input = page
        self.stack.addWidget(page)

    def _init_preview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        lbl_header = QLabel("Preview Loaded Text")
        lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_header.setFont(QFont("Helvetica", 16, QFont.Weight.Bold))
        
        self.preview_edit = QTextEdit()
        self.preview_edit.setFont(QFont("Consolas", 14))
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlaceholderText("No text loaded...")
        
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        self.btn_clean_only = self._create_styled_button("Clean Only", self._handle_clean, "background-color: #f39c12; color: white;", width=150)
        self.btn_clean_rewrite = self._create_styled_button("Clean + Rewrite", self._handle_clean_and_rewrite, "background-color: #e74c3c; color: white;", width=180)
        self.btn_back = self._create_styled_button("Back", self._go_to_input, "background-color: #95a5a6; color: white;", width=120)
        
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(self.btn_back)
        btn_layout.addWidget(self.btn_clean_only)
        btn_layout.addWidget(self.btn_clean_rewrite)
        
        layout.addWidget(lbl_header)
        layout.addWidget(self.preview_edit)
        layout.addWidget(btn_container)

        self.page_preview = page
        self.stack.addWidget(page)

    def _init_result_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        lbl_header = QLabel("Sanitization Results: Before vs After")
        lbl_header.setFont(QFont("Helvetica", 16, QFont.Weight.Bold))
        lbl_header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_ai_score = QLabel("AI Score: --/10")
        self.lbl_ai_score.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.lbl_ai_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ai_score.setStyleSheet("color: #7f8c8d;")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.before_edit = self._create_labeled_textarea("Original Text")
        self.after_edit = self._create_labeled_textarea("Cleaned Text")
        
        splitter.addWidget(self.before_edit['container'])
        splitter.addWidget(self.after_edit['container'])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        self.log_header = QLabel("Changes Log")
        self.log_header.setFont(QFont("Helvetica", 13, QFont.Weight.Bold))

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont("Consolas", 11))
        self.log_edit.setMaximumHeight(180)
        self.log_edit.setPlaceholderText("No changes detected.")

        action_container = QWidget()
        action_layout = QHBoxLayout(action_container)
        self.btn_copy = self._create_styled_button("Copy", self._handle_copy, "background-color: #2ecc71; color: white;")
        self.btn_new = self._create_styled_button("New Clean", self._handle_restart, "background-color: #3498db; color: white;")
        self.btn_close = self._create_styled_button("Close", self.close, "background-color: #7f8c8d; color: white;")
        
        action_layout.addStretch()
        action_layout.addWidget(self.btn_copy)
        action_layout.addWidget(self.btn_new)
        action_layout.addWidget(self.btn_close)
        action_layout.addStretch()

        layout.addWidget(lbl_header)
        layout.addWidget(self.lbl_ai_score)
        layout.addWidget(splitter)
        layout.addWidget(self.log_header)
        layout.addWidget(self.log_edit)
        layout.addWidget(action_container)

        self.page_result = page
        self.stack.addWidget(page)

    def _create_styled_button(self, text: str, callback, style: str, width: int = 180, height: int = 50) -> QPushButton:
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        btn.setFixedSize(width, height)
        btn.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
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
        label.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        
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
        print(f"DEBUG: Loaded text. Length: {len(self.raw_text)}")
        self.preview_edit.setText(text)
        self.stack.setCurrentIndex(1)

    def _go_to_input(self):
        self.stack.setCurrentIndex(0)
        self.raw_text = ""
        self.preview_edit.clear()

    def _handle_clean(self):
        print(f"DEBUG: Clean button clicked. raw_text length: {len(self.raw_text)}")
        if not self.raw_text:
            print("DEBUG: raw_text is empty, returning.")
            return

        try:
            print("DEBUG: Starting build_changes_log...")
            self.clean_text, self.change_log = build_changes_log(self.raw_text)
            
            self.before_edit['text_edit'].setText(self.raw_text)
            self.after_edit['text_edit'].setText(self.clean_text)
            self.lbl_ai_score.setText("AI Score: --/10")
            self.lbl_ai_score.setStyleSheet("color: #7f8c8d;")
            self._populate_changes_log()
            
            self.stack.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, "Cleaning Error", f"An error occurred during sanitization:\n{str(e)}")

    def _handle_clean_and_rewrite(self):
        print(f"DEBUG: Clean+Rewrite button clicked. raw_text length: {len(self.raw_text)}")
        if not self.raw_text:
            print("DEBUG: raw_text is empty, returning.")
            return

        self._set_loading_state(True)

        self.thread = QThread()
        self.worker = Worker(self.raw_text)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.progress_chunk.connect(self._on_chunk_received)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.before_edit['text_edit'].setText(self.raw_text)
        self.after_edit['text_edit'].clear()
        
        self.lbl_ai_score.setText("AI Score: --/10")
        self.lbl_ai_score.setStyleSheet("color: #7f8c8d;")
        
        self.stack.setCurrentIndex(2)
        
        self.worker.error.connect(self._on_worker_error)
        self.worker.error.connect(self.thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        
        self.thread.start()

    def _on_chunk_received(self, chunk):
        cursor = self.after_edit['text_edit'].textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.after_edit['text_edit'].setTextCursor(cursor)
        self.after_edit['text_edit'].ensureCursorVisible()

    def _on_worker_finished(self, clean_text, changes, ai_score):
        self.clean_text = clean_text
        self.change_log = changes
        
        self.lbl_ai_score.setText(f"AI Score: {ai_score}/10")
        
        if ai_score >= 7.0:
            self.lbl_ai_score.setStyleSheet("color: #c0392b; font-weight: bold;")
        elif ai_score >= 4.0:
            self.lbl_ai_score.setStyleSheet("color: #e67e22; font-weight: bold;")
        else:
            self.lbl_ai_score.setStyleSheet("color: #27ae60; font-weight: bold;")
        
        self.after_edit['text_edit'].setText(self.clean_text)
        self._populate_changes_log()
        
        self._set_loading_state(False)

    def _on_worker_error(self, error_msg):
        self._set_loading_state(False)
        QMessageBox.critical(self, "Processing Error", f"An error occurred:\n{error_msg}")

    def _set_loading_state(self, is_loading: bool):
        self.btn_clean_only.setEnabled(not is_loading)
        self.btn_clean_rewrite.setEnabled(not is_loading)
        self.btn_back.setEnabled(not is_loading)
        if is_loading:
            self.btn_clean_rewrite.setText("Processing...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            self.btn_clean_rewrite.setText("Clean + Rewrite")
            QApplication.restoreOverrideCursor()


    def _handle_copy(self):
        if not self.clean_text:
            QMessageBox.warning(self, "No Text", "There is no cleaned text to copy.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(self.clean_text)
        QMessageBox.information(self, "Success", "Cleaned text copied to clipboard!")

    def _populate_changes_log(self):
        if not self.change_log:
            self.log_header.setText("Changes Log — no changes detected")
            self.log_edit.clear()
            return

        count = len(self.change_log)
        self.log_header.setText(f"Changes Log — {count} change{'s' if count != 1 else ''} detected")

        lines = []
        for i, entry in enumerate(self.change_log, 1):
            lines.append(f"{i}. {entry.description}")

        self.log_edit.setPlainText('\n'.join(lines))

    def _handle_restart(self):
        self.raw_text = ""
        self.clean_text = ""
        self.change_log = []
        self.preview_edit.clear()
        self.before_edit['text_edit'].clear()
        self.after_edit['text_edit'].clear()
        self.log_edit.clear()
        self.log_header.setText("Changes Log")
        
        if hasattr(self, 'lbl_ai_score'):
            self.lbl_ai_score.setText("AI Score: --/10")
            self.lbl_ai_score.setStyleSheet("color: #7f8c8d;")
            
        self.stack.setCurrentIndex(0)

def _exception_hook(exc_type, exc_value, exc_tb):

    import traceback
    traceback.print_exception(exc_type, exc_value, exc_tb)



def main():
    sys.excepthook = _exception_hook
    
    app = QApplication(sys.argv)
    
    app.setStyle("Breeze")
    
    window = SanitizationApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()