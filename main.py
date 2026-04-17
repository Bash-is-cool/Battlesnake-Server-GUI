import sys

from PySide6.QtGui import QKeySequence

import gui_utils
import os
import subprocess
import importlib
import webbrowser
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
                               QLabel, QFrame, QFileDialog, QToolBar, QMessageBox,
                               QSpinBox, QGroupBox, QCheckBox)
from PySide6.QtCore import QThread, Signal, Slot, Qt

def check_and_install_dependencies():
    """Checks for paramiko and prompts user to install if missing."""
    try:
        importlib.import_module('paramiko')
    except ImportError:
        temp_app = QApplication(sys.argv)
        temp_app.setWindowIcon(QIcon(gui_utils.icon_path))

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Missing Dependency")
        msg.setText("The SSH Orchestrator requires the 'paramiko' library to talk to the Pi.")
        msg.setInformativeText("Would you like to install it now via pip?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        if msg.exec() == QMessageBox.Yes:
            try:
                # Runs 'pip install paramiko' in the background
                subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
                QMessageBox.information(None, "Success", "Paramiko installed! Please restart the application.")
                sys.exit(0)
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to install: {e}")
                sys.exit(1)
        else:
            QMessageBox.critical(None, "Critical Error", "Application cannot run without Paramiko.")
            sys.exit(1)


# Run the check
check_and_install_dependencies()

import paramiko


class SFTPWorker(QThread):
    status_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, host, user, password, local_path, remote_path):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        self.local_path = local_path
        self.remote_path = remote_path

    def run(self):
        try:
            transport = paramiko.Transport((self.host, 22))
            transport.connect(username=self.user, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            self.status_signal.emit(f"Uploading {os.path.basename(self.local_path)}...")
            sftp.put(self.local_path, self.remote_path)

            self.status_signal.emit(f"Successfully uploaded to {self.remote_path}")
            sftp.close()
            transport.close()
        except Exception as e:
            self.status_signal.emit(f"<font color='orange'>SFTP Error: {str(e)}</font>")
        finally:
            self.finished_signal.emit()

# --- The Logic: SSH Worker Thread ---
class SSHWorker(QThread):
    """Handles background communication with the Pi."""
    output_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, host, user, password, command):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        self.command = command

    def run(self):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the Pi
            client.connect(self.host, username=self.user, password=self.password, timeout=10)

            # Execute command and read real-time output
            stdin, stdout, stderr = client.exec_command(self.command)

            for line in stdout:
                self.output_signal.emit(line.strip())

            for line in stderr:
                self.output_signal.emit(f"ERROR: {line.strip()}")

            client.close()
        except Exception as e:
            self.output_signal.emit(f"SSH Failure: {str(e)}")
        finally:
            self.finished_signal.emit()

# --- The UI: Main Tournament Window ---
class BattlesnakeOrchestrator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        self.setup_toolbar()
        self.setup_connection_ui()
        self.setup_status_bar()

        # Path Editor
        self.setup_paths()

        # New Match Control Section
        self.setup_match_controls()

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc; font-family: Courier;")
        self.layout.addWidget(self.log_viewer)

        self.setup_action_buttons()
        self.worker = None

        self.setup_mini_terminal()

        self.cmd_history = []
        self.history_index = -1

    def setup_match_controls(self):
        """UI for configuring the Battlesnake CLI command."""
        self.match_group = QGroupBox("Match Configuration")
        match_layout = QHBoxLayout(self.match_group)

        # Snake Name Inputs
        self.snake_a_name = QLineEdit()
        self.snake_a_name.setPlaceholderText("Snake A (e.g. snek1.py)")
        self.snake_b_name = QLineEdit()
        self.snake_b_name.setPlaceholderText("Snake B (e.g. snek2.py)")

        # Board Size
        match_layout.addWidget(QLabel("Board Size:"))
        self.board_size = QSpinBox()
        self.board_size.setRange(7, 19)
        self.board_size.setValue(11)
        match_layout.addWidget(self.board_size)

        match_layout.addWidget(QLabel("Snake A URL/Name:"))
        match_layout.addWidget(self.snake_a_name)
        match_layout.addWidget(QLabel("vs"))
        match_layout.addWidget(self.snake_b_name)

        # Start Match Button
        self.btn_play = QPushButton("Run CLI Match")
        self.btn_play.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_play.clicked.connect(self.run_cli_match)
        match_layout.addWidget(self.btn_play)

        self.layout.addWidget(self.match_group)

    def setup_paths(self):
        self.path_group = QGroupBox("Paths")
        paths_layout = QHBoxLayout(self.path_group)

        self.remote_dir_input = QLineEdit()  # Default path
        self.remote_dir_input.setPlaceholderText("Remote Directory")

        paths_layout.addWidget(self.remote_dir_input)

        self.layout.addWidget(self.path_group)

    def execute_terminal_cmd(self):
        cmd = self.term_input.text().strip()
        if not cmd:
            return

        # Log the command to the viewer (with a distinct color)
        self.log_viewer.append(f"<font color='#50fa7b'>$ {cmd}</font>")

        # Clear the input for the next command
        self.term_input.clear()

        # Add to history
        self.cmd_history.append(cmd)
        self.history_index = len(self.cmd_history)

        # Run via SSH
        self.run_remote_cmd(cmd)

    def setup_mini_terminal(self):
        term_frame = QFrame()
        term_layout = QHBoxLayout(term_frame)
        term_layout.setContentsMargins(0, 5, 0, 5)

        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("Enter SSH command here... (e.g., ls -la or docker logs)")
        self.term_input.setStyleSheet("""
            background-color: #2b2b2b; 
            color: #50fa7b; 
            font-family: 'Courier New';
            border: 1px solid #444;
            padding: 4px;
        """)

        # Connect the 'Return' key to the execution method
        self.term_input.returnPressed.connect(self.execute_terminal_cmd)

        # Add a "Send" button
        self.btn_send_cmd = QPushButton("Execute")
        self.btn_send_cmd.clicked.connect(self.execute_terminal_cmd)

        term_layout.addWidget(QLabel(">"))  # Console prompt icon
        term_layout.addWidget(self.term_input)
        term_layout.addWidget(self.btn_send_cmd)

        self.layout.addWidget(term_frame)
        self.term_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Allows cycling through command history with arrow keys."""
        if obj == self.term_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Up:
                if self.cmd_history and self.history_index > 0:
                    self.history_index -= 1
                    self.term_input.setText(self.cmd_history[self.history_index])
                return True
            elif event.key() == Qt.Key_Down:
                if self.cmd_history and self.history_index < len(self.cmd_history) - 1:
                    self.history_index += 1
                    self.term_input.setText(self.cmd_history[self.history_index])
                else:
                    self.history_index = len(self.cmd_history)
                    self.term_input.clear()
                return True
        return super().eventFilter(obj, event)

    def run_cli_match(self):
        """Constructs and sends the 'battlesnake play' command to the Pi."""
        s1 = self.snake_a_name.text()
        s2 = self.snake_b_name.text()
        size = self.board_size.value()

        if not s1 or not s2:
            QMessageBox.warning(self, "Missing Data", "Enter both snake identifiers.")
            return

        # Note: This command assumes the snakes are already running as containers
        # Or you are using the CLI to point to their local URLs on the Pi network.
        cli_cmd = (
            f"battlesnake play -W {size} -H {size} "
            f"--name {s1} --url http://{s1}:8080 "
            f"--name {s2} --url http://{s2}:8080 --browser"
        )

        self.log_viewer.append(f"<b style='color:#3498db;'>Starting CLI Match:</b> {cli_cmd}")
        self.run_remote_cmd(cli_cmd)

    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.hide()
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        menu = self.menuBar()

        # File Actions
        file_menu = menu.addMenu("&File")

        upload_action = QAction("Upload Snake (main.py)", self)
        upload_action.setStatusTip("Upload a Python file to the Pi")
        upload_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_F))
        upload_action.triggered.connect(self.handle_file_upload)

        file_menu.addAction(upload_action)

        # Game Actions
        game_menu = menu.addMenu("&Game")
        view_action = QAction("View Live Game", self)
        view_action.triggered.connect(self.open_game_viewer)
        view_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_B))
        view_action.setStatusTip("View Live Game")
        game_menu.addAction(view_action)

        # View Menu
        view_menu = menu.addMenu("&View")

        toggle_toolbar_action = toolbar.toggleViewAction()
        toggle_toolbar_action.setText("Show Toolbar")
        view_menu.addAction(toggle_toolbar_action)

        toggle_match_action = QAction("Show Match Config", self)
        toggle_match_action.setCheckable(True)
        toggle_match_action.setChecked(True)  # It starts visible
        toggle_match_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_M))
        toggle_match_action.triggered.connect(self.toggle_match_config)
        view_menu.addAction(toggle_match_action)

        toggle_match_action = QAction("Show Path Config", self)
        toggle_match_action.setCheckable(True)
        toggle_match_action.setChecked(True)  # It starts visible
        toggle_match_action.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_P))
        toggle_match_action.triggered.connect(self.toggle_path_config)
        view_menu.addAction(toggle_match_action)

        toolbar.addAction(upload_action)
        toolbar.addAction(view_action)

    def toggle_match_config(self, visible):
        """Shows or hides the Match Configuration group box."""
        if visible:
            self.match_group.show()
        else:
            self.match_group.hide()

    def toggle_path_config(self, visible):
        """Shows or hides the Match Configuration group box."""
        if visible:
            self.path_group.show()
        else:
            self.path_group.hide()

    def setup_status_bar(self):
        """Adds a connection indicator dot to the status bar."""
        status_bar = self.statusBar()
        self.statusBar().setStyleSheet("QStatusBar::item { border: none; }")

        status_container = QWidget()
        container_layout = QHBoxLayout(status_container)
        container_layout.setContentsMargins(5, 0, 5, 0)
        container_layout.setSpacing(8)

        # The Connection Dot
        self.connection_dot = QLabel()
        self.connection_dot.setFixedSize(12, 12)

        # Start as Red
        self.update_connection_status("disconnected")

        container_layout.addWidget(QLabel("Status:"))
        container_layout.addWidget(self.connection_dot)

        # Add to the permanent right side
        status_bar.addPermanentWidget(status_container)

    def update_connection_status(self, state):
        """Helper to update the UI based on connection state."""
        colors = {
            "connected": "#27ae60",  # Green
            "disconnected": "#c0392b",  # Red
            "busy": "#f39c12"  # Orange
        }
        color = colors.get(state, "#7f8c8d")

        self.connection_dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 6px;
            border: 1px solid #2c3e50;
        """)

    def setup_connection_ui(self):
        conn_frame = QFrame()
        conn_layout = QHBoxLayout(conn_frame)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Your IP Address")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Remote Username")
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setPlaceholderText("Pi Password")

        self.remote_dir_input = QLineEdit()
        self.remote_dir_input.setPlaceholderText("Remote Directory")

        self.show_pw = QCheckBox("Show Password")
        self.show_pw.toggled.connect(self.toggle_password_visibility)

        conn_layout.addWidget(QLabel("Host:"))
        conn_layout.addWidget(self.ip_input)
        conn_layout.addWidget(QLabel("User:"))
        conn_layout.addWidget(self.user_input)
        conn_layout.addWidget(QLabel("Password:"))
        conn_layout.addWidget(self.pw_input)
        conn_layout.addWidget(self.show_pw)

        self.layout.addWidget(conn_frame)

    def toggle_password_visibility(self, checked):
        """Toggles the password field between hidden and plain text."""
        if checked:
            self.pw_input.setEchoMode(QLineEdit.Normal)
        else:
            self.pw_input.setEchoMode(QLineEdit.Password)

    def setup_action_buttons(self):
        btn_layout = QHBoxLayout()

        self.btn_test = QPushButton("Test Connection")
        self.btn_test.clicked.connect(self.test_connection)

        self.btn_docker = QPushButton("List Docker Containers")
        self.btn_docker.clicked.connect(lambda: self.run_remote_cmd("docker ps"))

        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(self.btn_docker)
        self.layout.addLayout(btn_layout)

    def handle_file_upload(self):
        if not self.pw_input.text():
            QMessageBox.warning(self, "Password Required", "Please enter the Pi password first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Snake Script", "", "Python Files (*.py)")
        if file_path:
            filename = os.path.basename(file_path)

            # Combine the directory from the UI with the filename
            remote_dir = self.remote_dir_input.text().strip()

            if remote_dir == '~':
                remote_dir = f"/home/{self.user_input.text()}/"

            if not remote_dir.endswith('/'):
                remote_dir += '/'
            remote_path = f"{remote_dir}{filename}"

            self.update_log(f"Starting upload to: {remote_path}")
            self.update_connection_status("busy")

            self.sftp_worker = SFTPWorker(
                self.ip_input.text(),
                self.user_input.text(),
                self.pw_input.text(),
                file_path,
                remote_path
            )

            self.sftp_worker.status_signal.connect(self.update_log)
            self.sftp_worker.finished_signal.connect(lambda: self.update_connection_status("connected"))

            # This triggers the Docker build automatically after upload
            #self.sftp_worker.finished_signal.connect(lambda: self.build_snake(name))

            self.sftp_worker.start()

    def build_snake(self, name):
        self.update_log(f"<b>Starting Docker build for: {name}...</b>")
        build_cmd = (
            f"cp /home/ubuntu/uploads/{name}.py /home/ubuntu/builder/logic.py && "
            f"docker build -t snake_{name} /home/ubuntu/builder"
        )
        self.run_remote_cmd(build_cmd)

    def run_remote_cmd(self, cmd):
        """Starts a background SSH thread for any command."""
        if cmd.lower() == "clear":
            self.log_viewer.clear()
            self.term_input.clear()
            return

        self.worker = SSHWorker(
            self.ip_input.text(),
            self.user_input.text(),
            self.pw_input.text(),
            cmd
        )
        self.worker.output_signal.connect(self.update_log)
        self.worker.start()

    def open_game_viewer(self):
        webbrowser.open("http://localhost:3000")

    @Slot(str)
    def update_log(self, text):
        """Appends text to the log viewer, color-coding errors."""
        # Convert to uppercase for a case-insensitive search
        upper_text = text.upper()
        is_error = any(word in upper_text for word in ["ERRNO", "ERROR:", "EXCEPTION:", "FAILURE"])

        # Check for error keywords
        if is_error:
            # Use HTML to make the line red
            formatted_text = f"<strong><font color='#ff5555'>{text}</font></strong>"
        elif text.startswith("$ "):
            # If it's a command sent from our mini-terminal, keep it green
            formatted_text = f"<font color='#50fa7b'>{text}</font>"
        else:
            # Standard white/gray text
            formatted_text = text

        self.log_viewer.append(formatted_text)

        # Ensure the log automatically scrolls to the bottom
        self.log_viewer.ensureCursorVisible()

    def test_connection(self):
        self.log_viewer.clear()
        self.run_remote_cmd("uname -a && uptime")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(gui_utils.icon_path))
    window = BattlesnakeOrchestrator()
    window.setWindowTitle("Battlesnake Orchestrator")
    window.show()
    sys.exit(app.exec())