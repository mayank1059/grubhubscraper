#!/usr/bin/env python3
"""
Demo script showcasing the Advanced Grubhub Menu Scraper features
"""

import json
import os
from datetime import datetime

def demo_scraped_data():
    """Demonstrate the rich data extracted by the scraper"""
    
    print("🍔 ADVANCED GRUBHUB MENU SCRAPER - FEATURE DEMO")
    print("=" * 60)
    
    # Check if we have scraped data
    scraped_dir = "scraped_data"
    if not os.path.exists(scraped_dir):
        print("❌ No scraped data found. Please run the scraper first!")
        return
    
    json_files = [f for f in os.listdir(scraped_dir) if f.endswith('.json')]
    
    if not json_files:
        print("❌ No JSON files found in scraped_data directory!")
        return
    
    print(f"📊 Found {len(json_files)} scraped restaurant(s)")
    print()
    
    # Load and analyze the first restaurant
    with open(os.path.join(scraped_dir, json_files[0]), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    restaurant_info = data.get('restaurant_info', {})
    menu = data.get('menu', {})
    
    # 1. Restaurant Information
    print("🏪 RESTAURANT INFORMATION:")
    print("-" * 30)
    print(f"Name: {restaurant_info.get('name', 'N/A')}")
    print(f"Address: {restaurant_info.get('address', 'N/A')}")
    print(f"Phone: {restaurant_info.get('phone', 'N/A')}")
    print(f"Rating: {restaurant_info.get('rating', 'N/A')} stars")
    print(f"Price Range: {restaurant_info.get('price_range', 'N/A')}")
    print(f"Cuisines: {', '.join(restaurant_info.get('cuisines', []))}")
    
    # Hours
    hours = restaurant_info.get('hours', {})
    if hours:
        print("Hours:")
        if hours.get('pickup'):
            print(f"  Pickup: {hours['pickup']}")
        if hours.get('delivery'):
            print(f"  Delivery: {hours['delivery']}")
    
    print()
    
    # 2. Menu Analysis
    print("📋 MENU ANALYSIS:")
    print("-" * 20)
    total_items = sum(len(items) for items in menu.values())
    print(f"Total Categories: {len(menu)}")
    print(f"Total Menu Items: {total_items}")
    print()
    
    print("Categories breakdown:")
    for category, items in menu.items():
        print(f"  • {category}: {len(items)} items")
    
    print()
    
    # 3. Sample Menu Items
    print("🍽️ SAMPLE MENU ITEMS:")
    print("-" * 25)
    
    item_count = 0
    for category, items in menu.items():
        if item_count >= 5:  # Show max 5 items
            break
        
        print(f"\n[{category}]")
        for item in items[:2]:  # Show 2 items per category
            if item_count >= 5:
                break
            
            print(f"  {item.get('name', 'Unknown')}")
            print(f"    Price: {item.get('price', 'N/A')}")
            if item.get('description'):
                desc = item['description'][:80] + "..." if len(item.get('description', '')) > 80 else item.get('description')
                print(f"    Description: {desc}")
            if item.get('image_url'):
                print(f"    Image: Available")
            print()
            item_count += 1
    
    # 4. Customer Reviews
    reviews = restaurant_info.get('reviews', [])
    if reviews:
        print("⭐ CUSTOMER REVIEWS:")
        print("-" * 20)
        print(f"Total Reviews: {len(reviews)}")
        print("\nSample Reviews:")
        
        for i, review in enumerate(reviews[:3]):  # Show first 3 reviews
            print(f"\n{i+1}. {review.get('reviewer_name', 'Anonymous')}")
            print(f"   Date: {review.get('date', 'N/A')}")
            print(f"   Review: {review.get('review_text', 'N/A')}")
    
    print()
    
    # 5. Data Structure
    print("📊 DATA STRUCTURE:")
    print("-" * 20)
    print("The scraper extracts comprehensive data including:")
    print("✅ Complete restaurant business information")
    print("✅ Full menu with categories and items")
    print("✅ Item details: names, prices, descriptions, images")
    print("✅ Customer reviews with ratings and dates")
    print("✅ Operating hours (pickup and delivery)")
    print("✅ Structured address information")
    print("✅ Restaurant metadata (cuisines, price range)")
    print()
    
    # 6. Export Capabilities
    print("📤 EXPORT CAPABILITIES:")
    print("-" * 25)
    print("✅ WordPress CSV for WP All Import (Voxel theme)")
    print("✅ Separate menu items CSV for detailed imports")
    print("✅ Raw JSON for custom processing")
    print("✅ Field mapping guide for easy setup")
    print()
    
    # 7. Advanced Features
    print("🚀 ADVANCED FEATURES:")
    print("-" * 22)
    print("✅ Handles dynamic React content loading")
    print("✅ Intelligent scrolling to load all menu items")
    print("✅ Category-aware menu extraction")
    print("✅ Parallel processing for multiple restaurants")
    print("✅ Real-time progress tracking")
    print("✅ Error handling and retry logic")
    print("✅ Professional Streamlit web interface")
    print()
    
    print("🎉 READY FOR PRODUCTION USE!")
    print("=" * 60)


def show_file_structure():
    """Show the file structure created by the scraper"""
    
    print("\n📁 FILE STRUCTURE:")
    print("-" * 20)
    
    # Check different directories
    directories = [
        ("scraped_data", "Raw scraped JSON files"),
        ("wp_import", "WordPress import files"),
        ("wp_export", "Streamlit export files")
    ]
    
    for dir_name, description in directories:
        if os.path.exists(dir_name):
            files = os.listdir(dir_name)
            print(f"\n{dir_name}/ - {description}")
            for file in files:
                file_path = os.path.join(dir_name, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"
                    print(f"  • {file} ({size_str})")
        else:
            print(f"\n{dir_name}/ - {description} (not created yet)")


if __name__ == "__main__":
    demo_scraped_data()
    show_file_structure()
    
    print("\n🔗 NEXT STEPS:")
    print("-" * 15)
    print("1. Run: streamlit run scraper_ui.py")
    print("2. Access the web interface at: http://localhost:8501")
    print("3. Paste Grubhub URLs and start scraping!")
    print("4. Use the export feature for WordPress import")
    print("5. Check the field mapping guide for Voxel setup") 