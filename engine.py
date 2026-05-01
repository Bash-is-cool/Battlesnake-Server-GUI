from models import SnakeContainer
import subprocess
import os


class DockerManager:
    """
    Handles all interaction with the Docker Desktop engine.
    This class bridges the gap between Python snake objects and actual OS-level containers.
    """

    def __init__(self, executor_func):
        """
        :param executor_func: A reference to the UI's command runner (run_remote_cmd).
        This allows the manager to pipe output directly back to the UI log.
        """
        self.execute = executor_func

    def create_dockerfile(self, snake: SnakeContainer):
        """
        Dynamically generates a Dockerfile based on the snake's specific entry point.
        This ensures each snake has a standard environment regardless of its folder structure.
        """
        df_content = (
            f"FROM python:3.11-slim\n"
            f"WORKDIR /app\n"
            f"COPY . .\n"
            f"RUN pip install --no-cache-dir -r requirements.txt\n"
            f"ENV PORT=8000\n"
            f"EXPOSE 8000\n"
            f"CMD [\"python\", \"{snake.filename}\"]"
        )
        # Writes the Dockerfile directly into the snake's source code directory
        with open(os.path.join(snake.directory, "Dockerfile"), "w") as f:
            f.write(df_content)

    def build_and_run(self, snake: SnakeContainer):
        """
        Full lifecycle method: Creates the environment, builds the image,
        and starts the container with the assigned port mapping.
        """
        self.create_dockerfile(snake)

        # Build image: 'snake_[name]' is used as the tag for organization
        self.execute(f"docker build -t snake_{snake.name} \"{snake.directory}\"")

        # Run container: Maps the unique snake.port (e.g. 8080) to internal port 8000
        self.execute(f"docker run -d -p {snake.port}:8000 --name {snake.name} snake_{snake.name}")

    def stop_and_remove(self, name):
        """
        Stops a running container and immediately deletes it to free up the
        container name and system resources.
        """
        self.execute(f"docker stop {name} && docker rm {name}")

    def get_active_containers(self):
        """
        Queries the Docker engine directly to get a list of what is currently running.
        Uses formatting strings to make parsing easier for the UI table.
        """
        try:
            # subprocess.CREATE_NO_WINDOW prevents CMD popups on Windows
            return subprocess.check_output(
                'docker ps --format "{{.Names}}|{{.Status}}"',
                shell=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).strip().split('\n')
        except:
            # Returns an empty list if Docker is down or no containers exist
            return []


class MatchEngine:
    """
    Handles the Battlesnake CLI game execution.
    Converts snake names/ports into the specific URLs required by the CLI.
    """

    def __init__(self, executor_func, name_map):
        """
        :param executor_func: Link to the UI's command runner.
        :param name_map: Reference to the main app's dictionary that stores Name -> Port.
        """
        self.execute = executor_func
        self.name_map = name_map

    def run_match(self, snake_a, snake_b, size):
        """
        Assembles and executes the Battlesnake CLI command to start a match.
        """

        def resolve(val):
            """
            Internal helper to determine if a user input is a known snake name,
             a raw port number, or a full URL.
            """
            # If it's a name we know (e.g. "MySnake"), look up its port
            if val in self.name_map:
                return f"http://localhost:{self.name_map[val]}", val

            # If it's a raw number (e.g. "8081"), treat it as a localhost port
            # Otherwise, assume the user provided a full URL (e.g. a remote snake)
            return (f"http://localhost:{val}" if val.isdigit() else val), "Custom"

        url_a, n_a = resolve(snake_a)
        url_b, n_b = resolve(snake_b)

        # --browser opens the Battlesnake visualizer in Chrome/Edge immediately
        cmd = f"battlesnake play -W {size} -H {size} --name {n_a} --url {url_a} --name {n_b} --url {url_b} --browser"
        self.execute(cmd)