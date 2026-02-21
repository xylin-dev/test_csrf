import os
import runpy
import sys
from pathlib import Path

site_dir = Path(__file__).parent
port = int(os.environ.get("PORT", 5002))
sys.argv = ["", str(port), "--bind", "127.0.0.1", "--directory", str(site_dir)]
runpy.run_module("http.server", run_name="__main__")
