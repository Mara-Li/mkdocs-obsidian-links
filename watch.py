import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import time
import signal
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# parse arg
import argparse

parser = argparse.ArgumentParser(description = "Watch for changes in a package and reinstall it.")
parser.add_argument("package_path", type = str, help = "Path to the package to watch.")
parser.add_argument("mkdocs_path", type = str, help = "Path to the MkDocs folder.")
args = parser.parse_args()
package_path = Path(args.package_path)
mkdocs_path = Path(args.mkdocs_path)
console = Console()

class PackageWatchHandler(FileSystemEventHandler):
    def __init__(self, package_path, mkdocs_path):
        self.package_path = package_path
        self.mkdocs_path = mkdocs_path
        self.mkdocs_process = None
        self.mkdocs_process = None
        self.log_thread = None
        self.stop_logging = False

    def log_output(self, process) :
        """Thread for logging MkDocs output with Rich."""
        while process.poll() is None :  # Check if process is still running
            line = process.stdout.readline()
            if line :
                # Utilise Rich pour afficher les logs stylisés
                if "ERROR" in line :
                    console.log(f"[bold red][MkDocs ERROR][/bold red]: {line.strip()}")
                elif "WARNING" in line :
                    console.log(f"[bold yellow][MkDocs WARNING][/bold yellow]: {line.strip()}")
                else :
                    console.log(f"[bold green][MkDocs][/bold green]: {line.strip()}")

    def start_mkdocs(self):
        """Démarre le serveur MkDocs avec python -m mkdocs."""
        console.print(Panel(f"Starting MkDocs server for {self.mkdocs_path}...", style = "bold blue"))
        self.mkdocs_process = subprocess.Popen(
                ["uv", "run", "mkdocs", "--color", "serve"],
            cwd=self.mkdocs_path,
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
                universal_newlines = True,
                bufsize = 1,
        )
        self.stop_logging = False
        self.log_thread = threading.Thread(target = self.log_output, args = (self.mkdocs_process,))
        self.log_thread.start()
        console.print(
                Panel("MkDocs server started at [bold blue]https://127.0.0.1:8000[/bold blue].", style = "bold green")
                )

    def stop_mkdocs(self) :
        """Stop the MkDocs server."""
        if self.mkdocs_process :
            console.print(Panel("Stopping MkDocs server...", style = "bold red"))
            self.stop_logging = True
            self.mkdocs_process.terminate()
            try :
                self.mkdocs_process.wait(timeout = 5)
            except subprocess.TimeoutExpired :
                os.kill(self.mkdocs_process.pid, signal.SIGKILL)
            if self.log_thread :
                self.log_thread.join()
            self.mkdocs_process = None
            console.print(Panel("MkDocs server stopped.", style = "bold red"))

    def restart_mkdocs(self) :
        """Restart the MkDocs server."""
        self.stop_mkdocs()
        self.start_mkdocs()

    def on_any_event(self, event) :
        """React to file changes."""
        if event.is_directory or not event.src_path.endswith(".py") :
            return
        console.print(Panel(f"Change detected in {event.src_path}. Reinstalling package...", style = "bold yellow"))
        subprocess.run(["uv", "pip", "install", "-e", self.package_path], check = True)
        self.restart_mkdocs()


if __name__ == "__main__":
    package_path = package_path  # Chemin vers le package
    mkdocs_path = mkdocs_path  # Chemin vers le dossier contenant MkDocs

    # Vérifie si le dossier MkDocs existe
    if not os.path.isdir(mkdocs_path):
        console.print(f"[bold red]Error:[/bold red] MkDocs path '{mkdocs_path}' does not exist.")
        exit(1)

    event_handler = PackageWatchHandler(package_path, mkdocs_path)
    observer = Observer()
    observer.schedule(event_handler, package_path, recursive=True)

    console.print(f"[bold green]Watching for changes in {package_path}...[/bold green]")
    event_handler.start_mkdocs()
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("[bold red]Shutting down...[/bold red]")
        observer.stop()
        event_handler.stop_mkdocs()
    observer.join()
