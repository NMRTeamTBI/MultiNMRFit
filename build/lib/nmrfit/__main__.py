import sys
import nmrfit.ui

# start CLI if arguments provided, otherwise switch to GUI
if len(sys.argv) > 1:
    nmrfit.ui.start_cli(sys.argv)
else:
    nmrfit.ui.start_gui()
