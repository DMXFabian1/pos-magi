import requests
import os
import subprocess
import sys
import logging
from core.config.config import UPDATE_URL

logging.basicConfig(filename="pos.log", level=logging.ERROR)

class Updater:
    def __init__(self, current_version="1.0.0"):
        self.current_version = current_version

    def check_for_updates(self):
        try:
            response = requests.get(UPDATE_URL, timeout=5)
            response.raise_for_status()
            version_data = dict(line.split("=") for line in response.text.strip().split("\n"))
            if version_data["version"] != self.current_version:
                return version_data["url"], version_data["version"]
            return None, None
        except Exception as e:
            logging.error(f"Error al verificar actualizaciones: {e}")
            return None, None

    def update_program(self, download_url, latest_version):
        try:
            new_exe = "exodia_new.exe"
            response = requests.get(download_url, stream=True, timeout=10)
            with open(new_exe, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            update_script = "update.bat"
            current_exe = sys.executable
            with open(update_script, "w") as f:
                f.write(f"""
                @echo off
                timeout /t 2
                del "{current_exe}"
                rename "{new_exe}" "{os.path.basename(current_exe)}"
                start "" "{current_exe}"
                del "%~f0"
                """)
            subprocess.Popen(update_script, shell=True)
            sys.exit(0)
        except Exception as e:
            logging.error(f"Error al actualizar: {e}")