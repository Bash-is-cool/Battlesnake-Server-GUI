import os

class SnakeContainer:
    """Represents a Battlesnake Docker instance."""
    def __init__(self, name, port, path):
        self.name = name
        self.port = port
        self.path = path
        self.directory = os.path.dirname(path)
        self.filename = os.path.basename(path)