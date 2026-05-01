import sys

import gui_utils
import os
import subprocess
import importlib
import shutil
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
                               QLabel, QFrame, QFileDialog, QMessageBox,
                               QSpinBox, QGroupBox, QCheckBox, QHeaderView, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Slot, Qt

# Global flag to track run mode
RUN_LOCAL = True

def check_local_windows_deps():
    """Specific checks for Docker Desktop and Battlesnake CLI on Windows."""
    missing = []

    # Check Battlesnake CLI (Checks for both .exe and raw command)
    if shutil.which("battlesnake.exe") is None and shutil.which("battlesnake") is None:
        missing.append("• Battlesnake CLI (Download the .exe and add to PATH)")

    # Check Docker
    if shutil.which("docker") is None:
        missing.append("• Docker Desktop (Not installed or not in PATH)")
    else:
        try:
            # Check if the Docker engine is actually RUNNING
            subprocess.run(["docker", "version"], check=True, capture_output=True, shell=True)
        except Exception:
            missing.append("• Docker Engine (Docker Desktop is installed but not STARTED)")

    if missing:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Local Mode Setup")
        msg.setText("Incomplete Local Environment:")
        msg.setInformativeText("\n".join(missing) + "\n\nPlease fix these or switch to Pi mode.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        return False
    return True


def check_run_mode():
    global RUN_LOCAL
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(gui_utils.icon_path))

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle("Run Mode")
    msg.setText("How would you like to run the orchestrator?")
    msg.setInformativeText("Running locally will use Docker on this Windows machine.\nRunning on the Pi uses SSH.")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    btn_local = msg.button(QMessageBox.Yes)
    btn_local.setText("Locally (Recommended)")
    btn_pi = msg.button(QMessageBox.No)
    btn_pi.setText("On the Pi (Advanced)")

    if msg.exec() == QMessageBox.Yes:
        RUN_LOCAL = True
        if not check_local_windows_deps():
            sys.exit(0)
    else:
        RUN_LOCAL = False
        try:
            importlib.import_module('paramiko')
        except ImportError:
            install_msg = QMessageBox()
            install_msg.setText("Paramiko missing. Install it to use Pi mode?")
            install_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            if install_msg.exec() == QMessageBox.Yes:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
                QMessageBox.information(None, "Success", "Installed! Restarting app...")
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                sys.exit(0)
    return app

app = check_run_mode()

# --- The UI: Main Tournament Window ---
from models import SnakeContainer
from engine import DockerManager, MatchEngine
from remote_manager import SSHWorker, SFTPWorker


class BattlesnakeOrchestrator(QMainWindow):
    def __init__(self):
        """
        Main Constructor: Initializes the logic engines, UI layout,
        and switches interface components based on the RUN_LOCAL flag.
        """
        super().__init__()
        # 1. Initialize Logic Objects (Dependency Injection)
        self.next_port = 8080
        self.name_to_port = {}
        self.docker = DockerManager(self.run_remote_cmd)
        self.match_engine = MatchEngine(self.run_remote_cmd, self.name_to_port)

        # 2. Window Geometry and Layout Setup
        self.setMinimumSize(900, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # 3. Conditional UI Construction
        if RUN_LOCAL:
            # Local Mode: Use Windows Docker and CLI
            self.setup_match_controls()
            self.setup_local_container_ui()
            self.refresh_containers()
        else:
            # Pi Mode: Use SSH, SFTP, and Remote Terminal
            self.setup_connection_ui()
            self.setup_match_controls()
            self.setup_paths()
            self.setup_action_buttons()
            self.setup_mini_terminal()
            self.cmd_history = []
            self.history_index = -1

        # 4. Global Logging Output
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("background-color: #1e1e1e; color: #dcdcdc; font-family: Courier;")
        self.layout.addWidget(self.log_viewer)

    def build_local_snake(self):
        """
        Extracts UI inputs to create a new SnakeContainer, assigns a unique port,
        and triggers the Docker build/run sequence via the DockerManager.
        """
        name = self.local_name_in.text().strip()
        path = self.local_path_in.text().strip()
        if not name or not path: return

        # Create model and increment port to avoid collisions
        snake = SnakeContainer(name, self.next_port, path)
        self.name_to_port[name] = self.next_port
        self.next_port += 1

        self.update_log(f"Building {name}...")
        self.docker.build_and_run(snake)  # Calls logic from engine.py
        self.refresh_containers()

    def run_cli_match(self):
        """
        Validates match inputs and hands off the execution to the MatchEngine.
        Resolves the snake names/URLs provided in the UI into a valid Battlesnake CLI command.
        """
        raw_a = self.snake_a_name.text().strip()
        raw_b = self.snake_b_name.text().strip()
        if not raw_a or not raw_b:
            QMessageBox.warning(self, "Missing Data", "Enter Snake Names or Ports.")
            return

        self.match_engine.run_match(raw_a, raw_b, self.board_size.value())

    def refresh_containers(self):
        """
        Queries the DockerManager for current container statuses and re-populates
        the QTableWidget with container names, status strings, and action buttons.
        """
        self.container_table.setRowCount(0)
        lines = self.docker.get_active_containers()
        for line in lines:
            n, s = line.split('|')
            row = self.container_table.rowCount()
            self.container_table.insertRow(row)
            self.container_table.setItem(row, 0, QTableWidgetItem(n))
            self.container_table.setItem(row, 1, QTableWidgetItem(s))

            # Add a 'Stop' button for each row dynamically
            btn = QPushButton("Stop/Remove")
            btn.clicked.connect(lambda ch=False, name=n: self.stop_local_container(name))
            self.container_table.setCellWidget(row, 2, btn)

    def stop_local_container(self, name):
        """
        Stops and removes a specific Docker container by name and removes it
        from the internal port-tracking dictionary.
        """
        self.docker.stop_and_remove(name)
        if name in self.name_to_port:
            del self.name_to_port[name]
        self.refresh_containers()

    def run_remote_cmd(self, cmd):
        """
        The central gateway for all commands. Executes locally via subprocess
        if RUN_LOCAL is True, otherwise spins up a background SSHWorker thread.
        """
        if cmd.lower() == "clear":
            self.log_viewer.clear()
            return

        if RUN_LOCAL:
            # Direct execution on local OS
            try:
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()
                if stdout: self.update_log(stdout)
                if stderr: self.update_log(f"ERROR: {stderr}")
            except Exception as e:
                self.update_log(f"Local Failure: {e}")
        else:
            # Offload to background thread to keep UI responsive
            self.worker = SSHWorker(self.ip_input.text(), self.user_input.text(),
                                    self.pw_input.text(), cmd)
            self.worker.output_signal.connect(self.update_log)
            self.worker.start()

    def setup_match_controls(self):
        """
        Builds the 'Match Configuration' UI group, including board size
        adjustment and snake identity inputs.
        """
        self.match_group = QGroupBox("Match Configuration")
        match_layout = QHBoxLayout(self.match_group)

        # UI Components for defining the game
        self.snake_a_name = QLineEdit()
        self.snake_a_name.setPlaceholderText("Snake A (e.g. mrt)")
        self.snake_b_name = QLineEdit()
        self.snake_b_name.setPlaceholderText("Snake B (e.g. silver)")

        self.board_size = QSpinBox()
        self.board_size.setRange(7, 19)
        self.board_size.setValue(11)

        match_layout.addWidget(QLabel("Board Size:"))
        match_layout.addWidget(self.board_size)
        match_layout.addWidget(QLabel("Snake A Name:"))
        match_layout.addWidget(self.snake_a_name)
        match_layout.addWidget(QLabel("vs Snake B Name:"))
        match_layout.addWidget(self.snake_b_name)

        self.btn_play = QPushButton("Run CLI Match")
        self.btn_play.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.btn_play.clicked.connect(self.run_cli_match)
        match_layout.addWidget(self.btn_play)

        self.layout.addWidget(self.match_group)

    def setup_paths(self):
        """Creates the path configuration UI specifically for Pi/Remote mode."""
        self.path_group = QGroupBox("Paths")
        paths_layout = QHBoxLayout(self.path_group)

        self.remote_dir_input = QLineEdit()
        self.remote_dir_input.setPlaceholderText("Remote Directory")

        paths_layout.addWidget(self.remote_dir_input)
        self.layout.addWidget(self.path_group)

    def execute_terminal_cmd(self):
        """
        Handles the submission from the mini-terminal input. Adds the command
        to local history and triggers execution.
        """
        cmd = self.term_input.text().strip()
        if not cmd:
            return

        # Visual feedback in the log
        self.log_viewer.append(f"<font color='#50fa7b'>$ {cmd}</font>")
        self.term_input.clear()

        # Update history for arrow-key cycling
        self.cmd_history.append(cmd)
        self.history_index = len(self.cmd_history)

        self.run_remote_cmd(cmd)

    def setup_mini_terminal(self):
        """
        Builds a console-like input field at the bottom of the UI for
        sending raw commands to the remote system.
        """
        term_frame = QFrame()
        term_layout = QHBoxLayout(term_frame)
        term_layout.setContentsMargins(0, 5, 0, 5)

        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("Enter SSH command here...")
        self.term_input.setStyleSheet("background-color: #2b2b2b; color: #50fa7b; font-family: 'Courier New';")
        self.term_input.returnPressed.connect(self.execute_terminal_cmd)

        self.btn_send_cmd = QPushButton("Execute")
        self.btn_send_cmd.clicked.connect(self.execute_terminal_cmd)

        term_layout.addWidget(QLabel(">"))
        term_layout.addWidget(self.term_input)
        term_layout.addWidget(self.btn_send_cmd)

        self.layout.addWidget(term_frame)
        self.term_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        """
        Special event listener for the mini-terminal. Allows the user to
        press UP/DOWN arrows to cycle through previous commands.
        """
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

    def setup_connection_ui(self):
        """Sets up the IP, Username, and Password input fields for SSH connectivity."""
        conn_frame = QFrame()
        conn_layout = QHBoxLayout(conn_frame)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Your IP Address")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Remote Username")
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setPlaceholderText("Pi Password")

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
        """Switches the password QLineEdit between Password and Normal echo modes."""
        self.pw_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def setup_action_buttons(self):
        """Creates standard utility buttons for listing containers or testing SSH connectivity."""
        btn_layout = QHBoxLayout()

        self.btn_test = QPushButton("Test Connection")
        self.btn_test.clicked.connect(self.test_connection)

        self.btn_docker = QPushButton("List Docker Containers")
        self.btn_docker.clicked.connect(lambda: self.run_remote_cmd("docker ps"))

        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(self.btn_docker)
        self.layout.addLayout(btn_layout)

    def handle_file_upload(self):
        """
        Opens a File Dialog to select a Python script and initiates a
        background SFTPWorker thread to transfer it to the Pi.
        """
        if not self.pw_input.text():
            QMessageBox.warning(self, "Password Required", "Please enter the Pi password first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Snake Script", "", "")
        if file_path:
            filename = os.path.basename(file_path)
            remote_dir = self.remote_dir_input.text().strip()

            # Default to home directory if ~ is used or input is empty
            if not remote_dir or remote_dir == '~':
                remote_dir = f"/home/{self.user_input.text()}/"
            if not remote_dir.endswith('/'):
                remote_dir += '/'

            # Paramiko requires full path including filename
            remote_path = f"{remote_dir}{filename}"

            self.update_log(f"Starting upload to: {remote_path}")
            self.sftp_worker = SFTPWorker(self.ip_input.text(), self.user_input.text(),
                                          self.pw_input.text(), file_path, remote_path)
            self.sftp_worker.status_signal.connect(self.update_log)
            self.sftp_worker.start()

    def build_snake(self, name):
        """
        Sends a composite SSH command to copy the uploaded script into the
        build environment and trigger a 'docker build'.
        """
        self.update_log(f"<b>Starting Docker build for: {name}...</b>")
        build_cmd = (
            f"cp /home/ubuntu/uploads/{name}.py /home/ubuntu/builder/logic.py && "
            f"docker build -t snake_{name} /home/ubuntu/builder"
        )
        self.run_remote_cmd(build_cmd)

    @Slot(str)
    def update_log(self, text):
        """
        Thread-safe UI slot that appends text to the log viewer.
        Applies HTML formatting based on keyword detection (e.g., Error = Red).
        """
        upper_text = text.upper()
        is_error = any(word in upper_text for word in ["ERRNO", "ERROR:", "EXCEPTION:", "FAILURE"])

        if is_error:
            formatted_text = f"<strong><font color='#ff5555'>{text}</font></strong>"
        elif text.startswith("$ "):
            formatted_text = f"<font color='#50fa7b'>{text}</font>"
        else:
            formatted_text = text

        self.log_viewer.append(formatted_text)
        self.log_viewer.ensureCursorVisible()

    def test_connection(self):
        """Clears logs and sends a basic system command to verify the SSH link is active."""
        self.log_viewer.clear()
        self.run_remote_cmd("uname -a && uptime")

    def setup_local_container_ui(self):
        """
        Builds the UI components for Local Mode, including a path browser
        and a table to monitor active Docker containers on the host machine.
        """
        self.local_group = QGroupBox("Local Container Manager")
        local_layout = QVBoxLayout(self.local_group)

        build_row = QHBoxLayout()
        self.local_name_in = QLineEdit()
        self.local_name_in.setPlaceholderText("Snake Name")
        self.local_path_in = QLineEdit()
        self.local_path_in.setPlaceholderText("Path to main.py...")

        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self.browse_local_file)

        btn_start = QPushButton("Build & Start")
        btn_start.clicked.connect(self.build_local_snake)
        btn_start.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")

        build_row.addWidget(self.local_name_in)
        build_row.addWidget(self.local_path_in)
        build_row.addWidget(btn_browse)
        build_row.addWidget(btn_start)
        local_layout.addLayout(build_row)

        # Set up the interactive container list
        self.container_table = QTableWidget(0, 3)
        self.container_table.setHorizontalHeaderLabels(["Name", "Status", "Actions"])
        self.container_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.container_table.setFixedHeight(150)
        local_layout.addWidget(self.container_table)

        btn_refresh = QPushButton("Refresh Container List")
        btn_refresh.clicked.connect(self.refresh_containers)
        local_layout.addWidget(btn_refresh)

        self.layout.addWidget(self.local_group)

    def browse_local_file(self):
        """Opens a QFileDialog to easily grab the path of a snake script on the Windows filesystem."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Script", "", "Python (*.py)")
        if path:
            self.local_path_in.setText(path)

if __name__ == "__main__":
    window = BattlesnakeOrchestrator()
    window.setWindowTitle(f"Battlesnake Orchestrator ({'Local' if RUN_LOCAL else 'Remote'})")

    window.show()
    sys.exit(app.exec())