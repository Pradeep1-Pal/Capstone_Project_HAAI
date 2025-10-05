import subprocess
import json

def is_model_downloaded(model_name):
    """
    Check if an Ollama model is already downloaded.
    
    Args:
        model_name (str): Name of the model (e.g., "llama3.2:3b")
    
    Returns:
        bool: True if model is downloaded, False otherwise
    """
    try:
        # Run 'ollama list' command to get all downloaded models
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output
        output = result.stdout.strip()
        
        # Check if model name exists in the list
        for line in output.split('\n')[1:]:  # Skip header line
            if line.strip() and model_name in line:
                print(f"✅ Model '{model_name}' is already downloaded")
                return True
        
        print(f"❌ Model '{model_name}' is not downloaded")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"Error checking models: {e}")
        print("Make sure Ollama is installed and running")
        return False
    except FileNotFoundError:
        print("Ollama is not installed or not in PATH")
        return False

def download_model(model_name, use_new_terminal=True):
    """
    Download an Ollama model.
    
    Args:
        model_name (str): Name of the model to download (e.g., "llama3.2:3b")
        use_new_terminal (bool): If True, opens a new terminal window for download
    
    Returns:
        bool: True if download was successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"🦙 Downloading model: {model_name}")
    print(f"{'='*60}\n")
    
    try:
        # Check if already downloaded
        if is_model_downloaded(model_name):
            print(f"Model '{model_name}' is already available")
            return True
        
        if use_new_terminal:
            # Open a new terminal window for the download
            import platform
            system = platform.system()
            
            if system == "Windows":
                # Windows: Use start command to open new cmd window
                command = f'start cmd /k "ollama pull {model_name} && echo. && echo Download complete! && pause"'
                subprocess.Popen(command, shell=True)
                print(f"✅ Opened new terminal window for downloading '{model_name}'")
                print("Check the new window for download progress")
                return True
                
            elif system == "Darwin":  # macOS
                # macOS: Use osascript to open new Terminal window
                command = f'''osascript -e 'tell application "Terminal" to do script "ollama pull {model_name} && echo && echo Download complete! && read -p \\"Press Enter to close...\\""' '''
                subprocess.Popen(command, shell=True)
                print(f"✅ Opened new terminal window for downloading '{model_name}'")
                return True
                
            elif system == "Linux":
                # Linux: Try common terminal emulators
                terminals = [
                    f"gnome-terminal -- bash -c 'ollama pull {model_name}; echo; echo Download complete!; read -p \"Press Enter to close...\"'",
                    f"konsole -e bash -c 'ollama pull {model_name}; echo; echo Download complete!; read -p \"Press Enter to close...\"'",
                    f"xterm -e bash -c 'ollama pull {model_name}; echo; echo Download complete!; read -p \"Press Enter to close...\"'",
                ]
                
                for terminal_cmd in terminals:
                    try:
                        subprocess.Popen(terminal_cmd, shell=True)
                        print(f"✅ Opened new terminal window for downloading '{model_name}'")
                        return True
                    except:
                        continue
                
                print("⚠️  Could not open new terminal. Downloading in current terminal...")
                use_new_terminal = False
            else:
                print("⚠️  Unknown OS. Downloading in current terminal...")
                use_new_terminal = False
        
        if not use_new_terminal:
            # Download in current terminal with real-time output
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output in real-time
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                print(f"\n✅ Successfully downloaded model: {model_name}")
                return True
            else:
                print(f"\n❌ Failed to download model: {model_name}")
                return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error downloading model: {e}")
        return False
    except FileNotFoundError:
        print("Ollama is not installed or not in PATH")
        print("Install Ollama from: https://ollama.ai")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        return False


if __name__ == "__main__":
    # Example 1: Check if a model is downloaded
    model = "qwen:0.5b"
    is_downloaded = is_model_downloaded(model)
    
    # Example 2: Download a model if not already downloaded
    if not is_downloaded:
        download_model(model)
    
   