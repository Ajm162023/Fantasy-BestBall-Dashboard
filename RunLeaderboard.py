import subprocess
import sys
import os

# Path to your app file
APP_FILE = "C:/Users/Alex Maggard/OneDrive/Desktop/Fantasy BestBall/FantasyBestBallLeaderBoard.py"

def run_streamlit():
    try:
        # Use sys.executable to ensure the same Python env is used
        subprocess.run([sys.executable, "-m", "streamlit", "run", APP_FILE], check=True)
    except KeyboardInterrupt:
        print("\nStopped manually.")

if __name__ == "__main__":
    run_streamlit()
