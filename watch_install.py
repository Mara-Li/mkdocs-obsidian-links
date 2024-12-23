from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import time
import signal

# parse arg
import argparse

parser = argparse.ArgumentParser(description = "Watch for changes in a package and reinstall it.")
parser.add_argument("package_path", type = str, help = "Path to the package to watch.")
parser.add_argument("mkdocs_path", type = str, help = "Path to the MkDocs folder.")
args = parser.parse_args()
package_path = args.package_path
mkdocs_path = args.mkdocs_path

class PackageWatchHandler(FileSystemEventHandler):
    def __init__(self, package_path, mkdocs_path):
        self.package_path = package_path
        self.mkdocs_path = mkdocs_path
        self.mkdocs_process = None

    def start_mkdocs(self):
        """Démarre le serveur MkDocs avec python -m mkdocs."""
        print("Starting MkDocs server...")
        self.mkdocs_process = subprocess.Popen(
            ["python", "-m", "mkdocs", "serve"],
            cwd=self.mkdocs_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        print("MkDocs server started.")

    def stop_mkdocs(self):
        """Arrête le serveur MkDocs proprement."""
        if self.mkdocs_process:
            print("Stopping MkDocs server...")
            self.mkdocs_process.terminate()
            try:
                self.mkdocs_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.kill(self.mkdocs_process.pid, signal.SIGKILL)
            print("MkDocs server stopped.")
            self.mkdocs_process = None

    def restart_mkdocs(self):
        """Redémarre le serveur MkDocs."""
        self.stop_mkdocs()
        self.start_mkdocs()

    def on_any_event(self, event):
        """Réagit aux modifications de fichiers."""
        if event.is_directory or not event.src_path.endswith(".py"):
            return
        print(f"Change detected in {event.src_path}. Reinstalling package...")
        subprocess.run(["pip", "install", "-e", self.package_path], check=True)
        self.restart_mkdocs()


if __name__ == "__main__":
    package_path = package_path  # Chemin vers le package
    mkdocs_path = mkdocs_path  # Chemin vers le dossier contenant MkDocs

    # Vérifie si le dossier MkDocs existe
    if not os.path.isdir(mkdocs_path):
        print(f"Error: MkDocs path '{mkdocs_path}' does not exist.")
        exit(1)

    event_handler = PackageWatchHandler(package_path, mkdocs_path)
    observer = Observer()
    observer.schedule(event_handler, package_path, recursive=True)

    print(f"Watching for changes in {package_path}...")
    event_handler.start_mkdocs()  # Lancer MkDocs au début
    observer.start()

    try:
        while True:
            # Lire les logs de MkDocs pendant que le script tourne
            if event_handler.mkdocs_process:
                output = event_handler.mkdocs_process.stdout.readline()
                if output:
                    print(f"[MkDocs]: {output.strip()}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        observer.stop()
        event_handler.stop_mkdocs()
    observer.join()
