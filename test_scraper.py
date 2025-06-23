#!/usr/bin/env python3
"""
Test script for the Grubhub scraper.
Run this to verify the scraper is working correctly.
"""

import os
import sys
import json

# Test URL - Rally's from the sample HTML
TEST_URL = "https://www.grubhub.com/restaurant/rallys-4154-lee-rd-cleveland/2007838"

print("Testing Grubhub Scraper...")
print(f"Test URL: {TEST_URL}")
print("-" * 50)

# Run the scraper
cmd = f'python bulk_grubhub_scraper.py -u "{TEST_URL}" -o test_output --no-headless --timeout 45'
print(f"Running: {cmd}")
result = os.system(cmd)

if result == 0:
    print("\n✅ Scraper ran successfully!")
    
    # Check if output file exists
    output_file = "test_output/rallys-4154-lee-rd-cleveland_menu.json"
    if os.path.exists(output_file):
        print(f"\n📄 Output file created: {output_file}")
        
        # Load and display summary
        with open(output_file, 'r') as f:
            menu = json.load(f)
        
        print(f"\n📊 Menu Summary:")
        print(f"   Categories: {len(menu)}")
        for category, items in menu.items():
            print(f"   - {category}: {len(items)} items")
        
        # Show first item as example
        if menu:
            first_cat = list(menu.keys())[0]
            if menu[first_cat]:
                print(f"\n🍔 Example item from '{first_cat}':")
                item = menu[first_cat][0]
                print(f"   Name: {item.get('name', 'N/A')}")
                print(f"   Price: {item.get('price', 'N/A')}")
                if item.get('description'):
                    print(f"   Description: {item['description'][:100]}...")
    else:
        print("\n❌ Output file not found!")
else:
    print("\n❌ Scraper failed!")
    print("\nTroubleshooting tips:")
    print("1. Make sure Chrome and ChromeDriver are installed")
    print("2. Install dependencies: pip install selenium beautifulsoup4 webdriver-manager")
    print("3. Try running with --no-headless to see what's happening")
    print("4. Check if the URL is accessible in your browser") 