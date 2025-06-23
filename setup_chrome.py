#!/usr/bin/env python3
"""
Chrome installation script for Streamlit Cloud deployment.
This handles Chrome and ChromeDriver installation when packages.txt fails.
"""

import os
import sys
import subprocess
import requests
import zipfile
import tempfile

def run_command(cmd):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {cmd}")
        print(f"Error: {e.stderr}")
        return False

def install_chrome():
    """Install Google Chrome."""
    print("Installing Google Chrome...")
    
    # Add Google's signing key
    if not run_command("wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -"):
        return False
    
    # Add Chrome repository
    if not run_command('echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'):
        return False
    
    # Update package list
    if not run_command("apt-get update"):
        return False
    
    # Install Chrome
    if not run_command("apt-get install -y google-chrome-stable"):
        return False
    
    return True

def install_chromedriver():
    """Install ChromeDriver."""
    print("Installing ChromeDriver...")
    
    try:
        # Get Chrome version
        result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
        chrome_version = result.stdout.strip().split()[-1].split('.')[0]
        
        # Get compatible ChromeDriver version
        driver_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
        response = requests.get(driver_url)
        driver_version = response.text.strip()
        
        # Download ChromeDriver
        download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_linux64.zip"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "chromedriver.zip")
            
            # Download
            response = requests.get(download_url)
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Move to /usr/local/bin
            chromedriver_path = os.path.join(temp_dir, "chromedriver")
            target_path = "/usr/local/bin/chromedriver"
            
            if os.path.exists(chromedriver_path):
                run_command(f"mv {chromedriver_path} {target_path}")
                run_command(f"chmod +x {target_path}")
                print(f"✓ ChromeDriver installed to {target_path}")
                return True
            else:
                print("✗ ChromeDriver binary not found in zip")
                return False
                
    except Exception as e:
        print(f"✗ ChromeDriver installation failed: {e}")
        return False

def check_installation():
    """Check if Chrome and ChromeDriver are properly installed."""
    print("Checking installation...")
    
    # Check Chrome
    try:
        result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
        print(f"✓ Chrome: {result.stdout.strip()}")
        chrome_ok = True
    except FileNotFoundError:
        print("✗ Chrome not found")
        chrome_ok = False
    
    # Check ChromeDriver
    try:
        result = subprocess.run(["chromedriver", "--version"], capture_output=True, text=True)
        print(f"✓ ChromeDriver: {result.stdout.strip()}")
        driver_ok = True
    except FileNotFoundError:
        print("✗ ChromeDriver not found")
        driver_ok = False
    
    return chrome_ok and driver_ok

def main():
    """Main installation function."""
    print("🚀 Setting up Chrome for Streamlit Cloud...")
    
    # Check if already installed
    if check_installation():
        print("✅ Chrome and ChromeDriver already installed!")
        return True
    
    # Install Chrome
    if not install_chrome():
        print("❌ Chrome installation failed!")
        return False
    
    # Install ChromeDriver
    if not install_chromedriver():
        print("❌ ChromeDriver installation failed!")
        return False
    
    # Final check
    if check_installation():
        print("✅ Chrome setup completed successfully!")
        return True
    else:
        print("❌ Chrome setup verification failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 