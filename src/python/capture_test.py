import subprocess
import os

def run_and_capture():
    try:
        # Run the test script and capture output in bytes
        res = subprocess.run(['../../venv/Scripts/python', 'test_accuracy.py'], 
                              capture_output=True, check=False)
        
        stdout = res.stdout.decode('utf-8', errors='replace')
        stderr = res.stderr.decode('utf-8', errors='replace')
        
        print("STDOUT:")
        print(stdout)
        print("\nSTDERR:")
        print(stderr)
        
        with open('debug_out.txt', 'w', encoding='utf-8') as f:
            f.write("STDOUT:\n")
            f.write(stdout)
            f.write("\nSTDERR:\n")
            f.write(stderr)
            
    except Exception as e:
        print(f"Error running capture: {e}")

if __name__ == "__main__":
    run_and_capture()
