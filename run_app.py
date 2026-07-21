import os
import sys
import streamlit.web.cli as stcli

if __name__ == '__main__':
    base_path = os.path.dirname(__file__)
    main_script = os.path.join(base_path, 'main.py')
    sys.argv = ["streamlit", "run", main_script, "--global.developmentMode=false"]
    sys.exit(stcli.main())