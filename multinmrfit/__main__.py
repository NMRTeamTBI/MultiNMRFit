import sys
import multinmrfit.ui_new as nui
import multinmrfit.io as nio
import multinmrfit.run as nrun
# # start CLI if arguments provided, otherwise switch to GUI
# if len(sys.argv) > 1:
#     multinmrfit.ui.start_cli(sys.argv)
# else:
#     multinmrfit.ui.start_gui()

if not len(sys.argv) == 2:
    print('gui')
    app = nui.App(user_input=nio.create_user_input())
    app.start()
else:
    print('cli')
    user_input = nio.load_config_file(None,config_file_path=sys.argv[1])        
    nrun.run_analysis(user_input,None)