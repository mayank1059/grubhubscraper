#!/bin/bash
# Install Chrome for Streamlit Cloud if packages.txt fails

echo "Installing Google Chrome..."

# Add Google's signing key
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -

# Add Chrome repository
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Update package list
apt-get update

# Install Chrome
apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

echo "Chrome installation complete!" 