import subprocess
import sys

subprocess.run([sys.executable, "-m", "streamlit", "run", "src/dashboard.py"], check=True)
