#!/usr/bin/env python3
import sys
import os
import tempfile
import shutil
import stat
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QCheckBox, QMessageBox, QTextEdit, QComboBox,
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt

APP_CATEGORIES = [
    "Utility", "Development", "Education", "Game", "Graphics",
    "Network", "Office", "AudioVideo", "System", "Other"
]

def find_terminal_cmd():
    # try common terminal emulators
    candidates = [
        ("x-terminal-emulator", "-e"),
        ("gnome-terminal", "--"),
        ("konsole", "-e"),
        ("xfce4-terminal", "-e"),
        ("mate-terminal", "-e"),
        ("tilix", "-e"),
        ("alacritty", "-e"),
        ("urxvt", "-e"),
        ("xterm", "-e"),
    ]
    for exe, flag in candidates:
        if shutil.which(exe):
            return exe, flag
    return None, None

class ShortcutMaker(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shortcut Maker — Forono")
        self.resize(640, 380)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Name
        self.name_edit = QLineEdit()
        layout.addLayout(self._row("Name *", self.name_edit, "Visible name in application menu"))
        # Exec path + picker
        self.exec_edit = QLineEdit()
        exec_btn = QPushButton("Browse")
        exec_btn.clicked.connect(self.pick_exec)
        h = QHBoxLayout()
        h.addWidget(self.exec_edit)
        h.addWidget(exec_btn)
        layout.addLayout(self._row("Exec path *", h, "Path to executable file (.bin, script, or any binary)"))
        # Arguments
        self.args_edit = QLineEdit()
        layout.addLayout(self._row("Arguments", self.args_edit, "For example: --debug or %U"))

        # Run in terminal
        self.terminal_chk = QCheckBox("Run in terminal")
        layout.addWidget(self.terminal_chk)

        # Icon
        self.icon_edit = QLineEdit()
        icon_btn = QPushButton("Browse")
        icon_btn.clicked.connect(self.pick_icon)
        h2 = QHBoxLayout()
        h2.addWidget(self.icon_edit)
        h2.addWidget(icon_btn)
        layout.addLayout(self._row("Icon (optional)", h2, "PNG/SVG or icon path"))

        # Category
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("")  # empty = no category
        for c in APP_CATEGORIES:
            self.cat_combo.addItem(c)
        layout.addLayout(self._row("Category", self.cat_combo, "For menu organization"))

        # Comment
        self.comment_edit = QLineEdit()
        layout.addLayout(self._row("Comment", self.comment_edit, "Short tooltip description"))

        # Target location radio
        radio_layout = QHBoxLayout()
        self.local_radio = QRadioButton("Local (recommended) — ~/.local/share/applications")
        self.local_radio.setChecked(True)
        self.system_radio = QRadioButton("System (all users) — /usr/share/applications (requires root)")
        radio_layout.addWidget(self.local_radio)
        radio_layout.addWidget(self.system_radio)
        layout.addLayout(self._row("Target location", radio_layout, ""))

        # Buttons: Test Run, Save
        btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Run")
        self.test_btn.clicked.connect(self.test_run)
        self.save_btn = QPushButton("Save Shortcut")
        self.save_btn.clicked.connect(self.save_shortcut)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)

        # Status / notes
        self.note = QLabel("")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        self.setLayout(layout)

    def _row(self, label_text, widget_or_layout, tooltip=""):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setMinimumWidth(140)
        if isinstance(widget_or_layout, QHBoxLayout):
            container = QWidget()
            container.setLayout(widget_or_layout)
            widget = container
        else:
            widget = widget_or_layout
        row.addWidget(lbl)
        row.addWidget(widget)
        if tooltip:
            widget.setToolTip(tooltip)
            lbl.setToolTip(tooltip)
        return row

    def pick_exec(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select executable")
        if path:
            self.exec_edit.setText(path)

    def pick_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select icon (PNG/SVG)")
        if path:
            self.icon_edit.setText(path)

    def clear_form(self):
        self.name_edit.clear()
        self.exec_edit.clear()
        self.args_edit.clear()
        self.icon_edit.clear()
        self.cat_combo.setCurrentIndex(0)
        self.comment_edit.clear()
        self.terminal_chk.setChecked(False)
        self.local_radio.setChecked(True)
        self.note.setText("")

    def validate(self):
        name = self.name_edit.text().strip()
        execp = self.exec_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Name cannot be empty.")
            return False

        if not execp:
            QMessageBox.warning(self, "Validation", "Exec path cannot be empty.")
            return False

        if not os.path.exists(execp):
            QMessageBox.warning(self, "Validation", f"Executable file not found:\n{execp}")
            return False

        # if not executable, ask to chmod +x (only if owned / writable)
        if not os.access(execp, os.X_OK):
            reply = QMessageBox.question(
                self, "Make executable?",
                "Selected file is not executable. Make it executable (chmod +x)?\n(System files may require root)",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                try:
                    os.chmod(execp, os.stat(execp).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except PermissionError:
                    QMessageBox.warning(self, "Permission denied",
                                        "Cannot change permission. Root access may be required.")
                    return False
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to change permission: {e}")
                    return False
        return True

    def build_desktop_content(self):
        name = self.name_edit.text().strip()
        execp = self.exec_edit.text().strip()
        args = self.args_edit.text().strip()
        comment = self.comment_edit.text().strip()
        icon = self.icon_edit.text().strip()
        category = self.cat_combo.currentText().strip()
        terminal = "true" if self.terminal_chk.isChecked() else "false"

        exec_line = execp
        if args:
            exec_line += " " + args

        cats = f"{category};" if category else ""
        content = [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={name}",
        ]
        if comment:
            content.append(f"Comment={comment}")
        content.append(f"Exec={exec_line}")
        if icon:
            content.append(f"Icon={icon}")
        content.append(f"Terminal={terminal}")
        if cats:
            content.append(f"Categories={cats}")
        content.append("StartupNotify=true")
        return "\n".join(content) + "\n"

    def test_run(self):
        if not self.validate():
            return
        execp = self.exec_edit.text().strip()
        args = self.args_edit.text().strip()
        run_in_terminal = self.terminal_chk.isChecked()

        if run_in_terminal:
            term, flag = find_terminal_cmd()
            if not term:
                QMessageBox.warning(self, "No terminal found",
                                    "Cannot find a terminal to run the command.")
                return
            cmd = [term, flag, execp]
            if args:
                cmd[-1] = cmd[-1] + " " + args
        else:
            cmd = [execp]
            if args:
                cmd.append(args)

        try:
            subprocess.Popen(cmd)
            QMessageBox.information(self, "Launched", "Application launched (Test Run).")
        except Exception as e:
            QMessageBox.warning(self, "Failed", f"Failed to launch application:\n{e}")

    def save_shortcut(self):
        if not self.validate():
            return
        content = self.build_desktop_content()
        name = self.name_edit.text().strip()
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()
        filename = safe_name.replace(" ", "_") + ".desktop"

        if self.local_radio.isChecked():
            target_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, filename)
            try:
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)
                os.chmod(dest_path, 0o755)
                self.note.setText(f"Shortcut created: {dest_path}")
                QMessageBox.information(self, "Saved", f"Shortcut created successfully:\n{dest_path}")
            except Exception as e:
                QMessageBox.warning(self, "Failed", f"Failed to launch application:\n{e}")

    def save_shortcut(self):
        if not self.validate():
            return
        content = self.build_desktop_content()
        name = self.name_edit.text().strip()
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()
        filename = safe_name.replace(" ", "_") + ".desktop"

        if self.local_radio.isChecked():
            target_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, filename)
            try:
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)
                os.chmod(dest_path, 0o755)
                self.note.setText(f"Shortcut created: {dest_path}")
                QMessageBox.information(self, "Saved", f"Shortcut created:\n{dest_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to write file:\n{e}")
        else:
            dest_dir = "/usr/share/applications"
            dest_path = os.path.join(dest_dir, filename)
            try:
                fd, tmp_path = tempfile.mkstemp(prefix="desktop_", suffix=".desktop", text=True)
                with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
                    tmpf.write(content)
                os.chmod(tmp_path, 0o755)

                pkexec = shutil.which("pkexec")
                if not pkexec:
                    QMessageBox.warning(self, "pkexec not found",
                                        "pkexec is not installed. Please install pkexec or use Local mode.")
                    os.remove(tmp_path)
                    return

                mv_cmd = [pkexec, "mv", tmp_path, dest_path]
                proc = subprocess.run(mv_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if proc.returncode != 0:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    msg = proc.stderr.strip() or "Unknown error"
                    QMessageBox.warning(self, "Failed", f"Failed to write system-wide shortcut:\n{msg}")
                    return

                chmod_cmd = [pkexec, "chmod", "755", dest_path]
                subprocess.run(chmod_cmd)
                self.note.setText(f"System shortcut created: {dest_path}")
                QMessageBox.information(self, "Saved (system)", f"System-wide shortcut created:\n{dest_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save system-wide shortcut:\n{e}")

def main():
    app = QApplication(sys.argv)
    w = ShortcutMaker()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
