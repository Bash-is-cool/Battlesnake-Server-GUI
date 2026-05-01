import paramiko
from PySide6.QtCore import QThread, Signal
import os


class SFTPWorker(QThread):
    """
    Handles file transfers to the Raspberry Pi in a background thread.
    Inheriting from QThread ensures the UI stays responsive during large uploads.
    """
    status_signal = Signal(str)  # Sends status updates (e.g., "Uploading...") to the UI
    finished_signal = Signal()  # Notifies the UI when the transfer is complete

    def __init__(self, host, user, password, local_path, remote_path):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        self.local_path = local_path
        self.remote_path = remote_path

    def run(self):
        """
        The entry point for the thread.
        Opens a transport tunnel, authenticates, and performs the SFTP PUT operation.
        """
        try:
            # 1. Establish the low-level network transport (SSH Port 22)
            transport = paramiko.Transport((self.host, 22))
            transport.connect(username=self.user, password=self.password)

            # 2. Initialize the SFTP client over that transport
            sftp = paramiko.SFTPClient.from_transport(transport)

            # 3. Perform the upload
            filename = os.path.basename(self.local_path)
            self.status_signal.emit(f"Uploading {filename}...")

            # Note: self.remote_path must include the target filename
            sftp.put(self.local_path, self.remote_path)

            self.status_signal.emit(f"Successfully uploaded to {self.remote_path}")

            # 4. Clean up connections
            sftp.close()
            transport.close()
        except Exception as e:
            # Catch network errors, permission issues, or incorrect paths
            self.status_signal.emit(f"<font color='orange'>SFTP Error: {str(e)}</font>")
        finally:
            # Always signal that the thread is done, even if it failed
            self.finished_signal.emit()


class SSHWorker(QThread):
    """
    Handles remote command execution (e.g., 'docker ps') in a background thread.
    Allows the UI to display terminal output line-by-line as it happens.
    """
    output_signal = Signal(str)  # Sends stdout/stderr lines back to the terminal log
    finished_signal = Signal()  # Notifies the UI when the command finishes

    def __init__(self, host, user, password, command):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        self.command = command

    def run(self):
        """
        Connects via SSH and streams the output of the requested command.
        """
        try:
            client = paramiko.SSHClient()
            # Automatically trust the Pi's SSH key (useful for local network setups)
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 1. Connect to the Pi with a 10-second timeout
            client.connect(self.host, username=self.user, password=self.password, timeout=10)

            # 2. Execute the non-interactive command
            # stdin:  Input stream (not used here)
            # stdout: Standard output stream (normal results)
            # stderr: Standard error stream (error messages)
            stdin, stdout, stderr = client.exec_command(self.command)

            # 3. Read stdout line-by-line and emit to the UI log
            # This 'for' loop blocks until a line is ready or the command ends
            for line in stdout:
                self.output_signal.emit(line.strip())

            # 4. Do the same for any error output
            for line in stderr:
                self.output_signal.emit(f"ERROR: {line.strip()}")

            # 5. Close the session
            client.close()
        except Exception as e:
            # Catch authentication failures or connection timeouts
            self.output_signal.emit(f"SSH Failure: {str(e)}")
        finally:
            # Ensure the UI knows this worker has finished its job
            self.finished_signal.emit()