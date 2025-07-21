import subprocess
import os
import sys

def main():
    """
    Launches the Streamlit application using a robust subprocess call.
    This avoids pathing issues across different operating systems.
    """
    # Get the absolute path to the main Streamlit script.
    project_root = os.path.dirname(os.path.abspath(__file__))
    app_file = os.path.join(project_root, "src", "app", "Home.py")

    # Check if the file exists before trying to run it
    if not os.path.exists(app_file):
        print(f"Error: Application file not found at '{app_file}'", file=sys.stderr)
        sys.exit(1)

    # Command to execute. Using sys.executable ensures we use the same Python env.
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_file,
        "--global.developmentMode=false",
        f"--server.runOnSave=true"
    ]

    print(f"Starting application... Command: {' '.join(command)}")
    
    try:
        # Run the command. The current process will be replaced by Streamlit.
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'streamlit' could not be run. Is it installed in your environment?", file=sys.stderr)
        print(f"Attempting to run from: {sys.executable}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
