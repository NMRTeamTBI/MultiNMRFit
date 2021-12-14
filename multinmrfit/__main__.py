import sys
import multinmrfit.ui

# start CLI if arguments provided, otherwise switch to GUI
if len(sys.argv) > 1:
    multinmrfit.ui.start_cli(sys.argv)
else:
    multinmrfit.ui.start_gui()
