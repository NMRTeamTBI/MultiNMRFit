import sys
import multinmrfit.ui as nui
import multinmrfit.io as nio
import multinmrfit.run as nrun


if not len(sys.argv) == 2:
    app = nui.App(user_input=nio.create_user_input())
    app.start()
else:
    user_input = nio.load_config_file(None,config_file_path=sys.argv[1]) 
    user_input = nio.check_input_file(user_input,None)       
    nrun.run_analysis(user_input,None)
