#!/usr/bin/env python3
"""
Deployment Setup Script for Grubhub Scraper
"""

import os
import subprocess

def main():
    print("🍔 Grubhub Scraper Deployment Setup")
    print("=" * 40)
    
    # Check if git is initialized
    try:
        subprocess.run(['git', 'status'], check=True, capture_output=True)
        print("✅ Git repository exists")
    except:
        print("🔧 Initializing Git repository...")
        subprocess.run(['git', 'init'], check=True)
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)
        print("✅ Git repository initialized")
    
    # Create .gitignore if not exists
    if not os.path.exists('.gitignore'):
        with open('.gitignore', 'w') as f:
            f.write("""__pycache__/
*.pyc
.env
.vscode/
scraped_data/
wp_import/
wp_export/
*.log
""")
        print("✅ .gitignore created")
    
    # Check required files
    required_files = ['requirements.txt', 'packages.txt', 'Procfile', 'runtime.txt']
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
    
    print("\n🚀 Ready for deployment!")
    print("\nOptions:")
    print("1. Streamlit Cloud: https://share.streamlit.io")
    print("2. Railway: https://railway.app") 
    print("3. Render: https://render.com")

if __name__ == "__main__":
    main() 