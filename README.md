# Battlesnake Orchestrator

A dual-mode GUI application designed to simplify the development, deployment, and testing of Battlesnakes. Whether you are developing locally on **Windows** using Docker Desktop or deploying to a **Raspberry Pi** via SSH, this tool orchestrates the entire lifecycle of a snake.

## Key Features

*   **Dual Mode Support**: Toggle between Local (Windows) and Remote (Pi) modes at startup.
*   **Automated Dockerization**: Automatically generates Dockerfiles and manages container builds for your snakes.
*   **Integrated Match Engine**: A GUI wrapper for the Battlesnake CLI to run games and open the visualizer in your browser automatically.
*   **Remote Management**: Full SFTP support for uploading snake logic and an integrated SSH mini-terminal for real-time debugging.
*   **Non-Blocking UI**: Uses background worker threads (`QThread`) for network and system tasks to keep the interface responsive.

---

##  Prerequisites

### Local Mode (Windows)
*   **Docker Desktop**: Installed, running, and accessible via CLI.
*   **Battlesnake CLI**: `battlesnake.exe` must be installed and added to your System `PATH`.
*   **Python 3.10+**: For running the application.

### Remote Mode (Raspberry Pi)
*   **SSH Access**: Enable SSH on your Pi and ensure it is reachable on your local network.
*   **Docker**: Installed on the Raspberry Pi.
*   **Paramiko**: The app will offer to install this automatically for SSH/SFTP communication if it isn't found.

---

##  Project Structure

*   **`main.py`**: The entry point. Handles UI initialization, mode selection logic, and dependency checks.
*   **`engine.py`**: Contains `DockerManager` for container lifecycles and `MatchEngine` for CLI game execution.
*   **`remote_manager.py`**: Houses the `SSHWorker` and `SFTPWorker` thread logic for remote operations.
*   **`models.py`**: Defines the `SnakeContainer` data structure used across the app.
*   **`gui_utils.py`**: UI helper functions, asset path management, and icons.

---

##  Getting Started

1.  **Download the EXE from the releases page**
2.  **Select Run Mode**:
    *   **Locally**: The app will perform a check for Docker and CLI dependencies.
    *   **On the Pi**: Enter your IP, User, and Password to establish a secure connection.

---

## How to Run a Match

### Step 1: Deploy Snakes
*   **Local**: Use the **Browse** button to select your snake script, then click **Build & Start**. This builds a Docker image and runs the container on a unique port.
*   make sure that the main.py file has the proper `requirements.txt` and `server.py` in the same folder
*   **Remote**: Use the **Upload** tool to send your `.py` files to the Pi, then use the build buttons to dockerize them remotely.

### Step 2: Configure the Match
*   **Setup**: In **Match Configuration**, enter the names of your running snakes (e.g., `my_snake` vs `enemy_snake`).
*   **Board**: Select the **Board Size** (default is 11x11).
*   **Execution**: Click **Run CLI Match**. Your default browser will open a new tab with the game visualization.

### AI Use
* **Debuging**
* **Commenting**
* **Some help with more complex libraries** such as `paramiko` for ssh
