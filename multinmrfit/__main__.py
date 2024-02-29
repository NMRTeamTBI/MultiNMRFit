from subprocess import run
from pathlib import Path
import multinmrfit

def main():
    path_to_app = Path(multinmrfit.__file__).parent
    path_to_app = path_to_app / "ui" / "01_Inputs_&_Outputs.py"
    run(["streamlit", "run", str(path_to_app)])

if __name__ == '__main__':
    main()