from subprocess import run
from pathlib import Path
import multinmrfit
from threading import Thread
import requests

def get_last_version():
    """Get last multinmrfit version."""
    try:
        pf_path = Path(multinmrfit.__file__).parent
        # Get the version from pypi
        response = requests.get('https://pypi.org/pypi/multinmrfit/json')
        latest_version = response.json()['info']['version']
        with open(str(Path(pf_path, "last_version.txt")), "w") as f:
            f.write(latest_version)
    except Exception:
        pass


def main():
    thread = Thread(target=get_last_version)
    thread.start()
    path_to_app = Path(multinmrfit.__file__).parent
    path_to_app = path_to_app / "ui" / "01_Inputs_&_Outputs.py"
    run(["streamlit", "run", str(path_to_app), "--server.maxUploadSize", "4096"])


if __name__ == '__main__':
    main()
