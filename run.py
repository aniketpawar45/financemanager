import subprocess
import sys
import time

def auto_install_dependencies():
    print("🔄 Executing the Pre-Release Protocol for Python 3.14...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", 
        "--pre", "--upgrade", "-r", "requirements.txt", "--quiet"
    ])
    print("✅ Experimental dependencies loaded.")

if __name__ == "__main__":
    auto_install_dependencies()
    time.sleep(1)
    
    from app.main import main
    main()
