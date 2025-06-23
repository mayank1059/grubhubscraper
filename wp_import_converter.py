#!/usr/bin/env python3
"""
WP All Import Converter for Voxel Theme
Converts scraped Grubhub data to CSV/XML format for WordPress import
"""

import json
import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import argparse
from typing import Dict, List
import re


def clean_text(text: str) -> str:
    """Clean text for import - remove special characters, normalize whitespace."""
    if not text:
        return ""
    
    # Ensure text is properly decoded as UTF-8
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    
    # Fix common encoding issues (comprehensive list)
    replacements = {
        'â€¢': '•',    # Bullet points
        'â€™': "'",    # Right single quotation mark
        'â€˜': "'",    # Left single quotation mark
        'â€œ': '"',    # Left double quotation mark
        'â€': '"',     # Right double quotation mark
        'â€"': '–',    # En dash
        'â€"': '—',    # Em dash
        'â€¦': '...',  # Horizontal ellipsis
        'Â': '',       # Non-breaking space artifacts
        'â': '',       # Weird a characters
        'Ã¡': 'á',     # a with acute
        'Ã©': 'é',     # e with acute
        'Ã­': 'í',     # i with acute
        'Ã³': 'ó',     # o with acute
        'Ãº': 'ú',     # u with acute
        'Ã±': 'ñ',     # n with tilde
        'Ã¼': 'ü',     # u with diaeresis
        'Ã¶': 'ö',     # o with diaeresis
        'Ã¤': 'ä',     # a with diaeresis
        'Ã§': 'ç',     # c with cedilla
        'â„¢': '™',    # Trademark symbol
        'Â®': '®',     # Registered trademark
        'Â©': '©',     # Copyright symbol
        'Â°': '°',     # Degree symbol
        'âˆš': '√',     # Square root
        'â‰¤': '≤',     # Less than or equal
        'â‰¥': '≥',     # Greater than or equal
        'Ã—': '×',     # Multiplication sign
        'Ã·': '÷',     # Division sign
    }
    
    # Apply all replacements
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    # Remove carriage returns and normalize whitespace
    text = re.sub(r'\r\n|\r|\n', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove or escape problematic characters for CSV
    text = text.replace('"', '""')  # Escape quotes for CSV
    
    # Remove leading bullet point if present
    if text.startswith('•'):
        text = text.lstrip('•').strip()
    
    return text


def format_hours(hours_dict: Dict) -> str:
    """Format hours dictionary into readable string."""
    if not hours_dict:
        return ""
    
    hours_parts = []
    if hours_dict.get('pickup'):
        hours_parts.append(f"Pickup: {hours_dict['pickup']}")
    if hours_dict.get('delivery'):
        hours_parts.append(f"Delivery: {hours_dict['delivery']}")
    
    return " | ".join(hours_parts)


def format_cuisines(cuisines_list: List) -> str:
    """Format cuisines list into comma-separated string."""
    if not cuisines_list:
        return ""
    return ", ".join(cuisines_list)


def format_reviews(reviews_list: List) -> str:
    """Format reviews into readable text."""
    if not reviews_list:
        return ""
    
    formatted_reviews = []
    for review in reviews_list[:5]:  # Limit to 5 reviews
        reviewer = review.get('reviewer_name', 'Anonymous')
        date = review.get('date', '')
        text = review.get('review_text', '')
        
        if text:
            formatted_reviews.append(f"{reviewer} ({date}): {text}")
    
    return " | ".join(formatted_reviews)


def convert_to_csv(json_files: List[str], output_file: str = "restaurants_import.csv"):
    """Convert JSON files to CSV format for WP All Import."""
    
    # Define CSV headers for Voxel theme fields
    headers = [
        'post_title',           # Restaurant name
        'post_content',         # Description
        'post_status',          # publish
        'post_type',            # your custom post type
        'restaurant_address',   # Address
        'restaurant_phone',     # Phone
        'restaurant_rating',    # Rating
        'restaurant_hours',     # Hours
        'restaurant_cuisines',  # Cuisines/Categories
        'restaurant_price_range', # Price range
        'restaurant_reviews',   # Reviews
        'restaurant_url',       # Original URL
        'menu_categories',      # Menu categories count
        'menu_items_total',     # Total menu items
        'menu_data',           # Full menu JSON
        'featured_image',       # Restaurant image
        'gallery_images',       # Menu item images
        'latitude',            # Coordinates
        'longitude',           # Coordinates
        'city',                # City
        'state',               # State
        'zip_code',            # ZIP
        'delivery_fee',        # Delivery info
        'delivery_time',       # Delivery time
    ]
    
    rows = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            restaurant_info = data.get('restaurant_info', {})
            menu = data.get('menu', {})
            
            # Extract structured address
            structured_addr = restaurant_info.get('structured_address', {})
            
            # Collect menu item images
            images = []
            for category, items in menu.items():
                for item in items:
                    if item.get('image_url'):
                        images.append(item['image_url'])
            
            # Create description from menu highlights
            description_parts = []
            if restaurant_info.get('cuisines'):
                description_parts.append(f"Serving {format_cuisines(restaurant_info['cuisines'])}")
            
            if menu:
                popular_items = []
                for category, items in list(menu.items())[:3]:  # First 3 categories
                    if items:
                        popular_items.append(f"{category}: {items[0]['name']}")
                if popular_items:
                    description_parts.append(f"Popular items include {', '.join(popular_items)}")
            
            description = ". ".join(description_parts) + "."
            
            row = {
                'post_title': clean_text(restaurant_info.get('name', '')),
                'post_content': clean_text(description),
                'post_status': 'publish',
                'post_type': 'restaurant',  # Change this to your Voxel post type
                'restaurant_address': clean_text(restaurant_info.get('address', '')),
                'restaurant_phone': clean_text(restaurant_info.get('phone', '')),
                'restaurant_rating': restaurant_info.get('rating', ''),
                'restaurant_hours': clean_text(format_hours(restaurant_info.get('hours', {}))),
                'restaurant_cuisines': clean_text(format_cuisines(restaurant_info.get('cuisines', []))),
                'restaurant_price_range': restaurant_info.get('price_range', ''),
                'restaurant_reviews': clean_text(format_reviews(restaurant_info.get('reviews', []))),
                'restaurant_url': data.get('url', ''),
                'menu_categories': len(menu),
                'menu_items_total': sum(len(items) for items in menu.values()),
                'menu_data': json.dumps(menu, ensure_ascii=False),  # Full menu as JSON
                'featured_image': '',  # You can add restaurant image URL here
                'gallery_images': '|'.join(images[:10]),  # Limit to 10 images
                'latitude': '',  # Add if you have coordinates
                'longitude': '',  # Add if you have coordinates
                'city': structured_addr.get('city', ''),
                'state': structured_addr.get('state', ''),
                'zip_code': structured_addr.get('zip', ''),
                'delivery_fee': restaurant_info.get('delivery_info', {}).get('delivery_fee', ''),
                'delivery_time': restaurant_info.get('delivery_info', {}).get('delivery_time', ''),
            }
            
            rows.append(row)
            print(f"Processed: {restaurant_info.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue
    
    # Write CSV file
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ CSV file created: {output_file}")
    print(f"✓ Processed {len(rows)} restaurants")
    return output_file


def create_menu_items_csv(json_files: List[str], output_file: str = "menu_items_import.csv"):
    """Create separate CSV for menu items with restaurant relationship."""
    
    headers = [
        'post_title',           # Item name
        'post_content',         # Item description
        'post_status',          # publish
        'post_type',            # menu_item
        'parent_restaurant',    # Restaurant name/ID
        'item_price',           # Price
        'item_category',        # Menu category
        'item_description',     # Description
        'item_image',           # Image URL
        'item_id',             # Original item ID
        'restaurant_name',      # For reference
    ]
    
    rows = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            restaurant_info = data.get('restaurant_info', {})
            menu = data.get('menu', {})
            restaurant_name = restaurant_info.get('name', 'Unknown')
            
            for category, items in menu.items():
                for item in items:
                    row = {
                        'post_title': clean_text(item.get('name', '')),
                        'post_content': clean_text(item.get('description', '')),
                        'post_status': 'publish',
                        'post_type': 'menu_item',  # Change this to your Voxel post type
                        'parent_restaurant': restaurant_name,
                        'item_price': item.get('price', ''),
                        'item_category': category,
                        'item_description': clean_text(item.get('description', '')),
                        'item_image': item.get('image_url', ''),
                        'item_id': item.get('id', ''),
                        'restaurant_name': restaurant_name,
                    }
                    rows.append(row)
            
            print(f"Processed menu items for: {restaurant_name}")
            
        except Exception as e:
            print(f"Error processing menu items from {json_file}: {e}")
            continue
    
    # Write CSV file
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Menu items CSV created: {output_file}")
    print(f"✓ Processed {len(rows)} menu items")
    return output_file


def create_voxel_mapping_guide(output_file: str = "voxel_field_mapping.txt"):
    """Create a guide for mapping fields in WP All Import to Voxel theme."""
    
    guide = """
# VOXEL THEME FIELD MAPPING GUIDE FOR WP ALL IMPORT

## RESTAURANT FIELDS MAPPING:

### Basic WordPress Fields:
- post_title → Restaurant Name
- post_content → Restaurant Description  
- post_status → publish
- post_type → [your-restaurant-post-type] (e.g., 'restaurant', 'listing')

### Voxel Custom Fields (adjust field names to match your Voxel setup):
- restaurant_address → Address field
- restaurant_phone → Phone field
- restaurant_rating → Rating field
- restaurant_hours → Hours field
- restaurant_cuisines → Categories/Cuisines field
- restaurant_price_range → Price Range field
- restaurant_reviews → Reviews field
- city → City field
- state → State field
- zip_code → ZIP Code field
- delivery_fee → Delivery Fee field
- delivery_time → Delivery Time field

### Images:
- featured_image → Featured Image field
- gallery_images → Gallery field (pipe-separated URLs)

### Menu Data:
- menu_categories → Number of menu categories
- menu_items_total → Total menu items count
- menu_data → Full menu JSON (for custom processing)

## WP ALL IMPORT SETUP STEPS:

1. **Install Required Plugins:**
   - WP All Import Pro
   - Voxel Theme

2. **Create Import:**
   - Go to All Import → New Import
   - Upload your CSV file: restaurants_import.csv
   - Select "New Items" and your restaurant post type

3. **Map Fields:**
   - Drag CSV columns to corresponding Voxel fields
   - Use the field names above as reference
   - For repeating fields (like menu items), use the menu_data JSON

4. **Advanced Mapping:**
   - For gallery images: Use "pipe" (|) as delimiter
   - For menu JSON: Create custom function to parse menu_data
   - For coordinates: Use geocoding service if needed

5. **Import Settings:**
   - Set "Update existing records" if re-importing
   - Configure image handling for gallery
   - Set up scheduling if needed

## MENU ITEMS IMPORT (OPTIONAL):

If you want separate menu item posts:
1. Import menu_items_import.csv as separate post type
2. Use parent_restaurant field to link to restaurant posts
3. Map item fields to your menu item custom fields

## CUSTOM FUNCTIONS (if needed):

Add to functions.php for advanced processing:

```php
// Parse menu JSON data
function parse_menu_data($menu_json) {
    $menu = json_decode($menu_json, true);
    // Process menu data as needed
    return $menu;
}

// Format hours display
function format_restaurant_hours($hours_string) {
    // Custom formatting logic
    return $hours_string;
}
```

## TESTING:
1. Start with a small test import (1-2 restaurants)
2. Verify all fields are mapping correctly
3. Check frontend display in Voxel theme
4. Adjust field mappings as needed
5. Run full import

## TROUBLESHOOTING:
- If images don't import: Check URL accessibility
- If custom fields missing: Verify Voxel field names
- If formatting issues: Adjust CSV data cleaning
- If performance issues: Import in smaller batches
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f"✓ Voxel mapping guide created: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert scraped Grubhub data to WordPress import format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert all JSON files in scraped_data directory
  python wp_import_converter.py

  # Convert specific files to CSV
  python wp_import_converter.py --files file1.json file2.json --format csv

  # Create menu items import
  python wp_import_converter.py --menu-items
        """
    )
    
    parser.add_argument(
        "--files",
        nargs="*",
        help="Specific JSON files to convert (default: all files in scraped_data/)"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "both"],
        default="csv",
        help="Output format (default: csv)"
    )
    parser.add_argument(
        "--menu-items",
        action="store_true",
        help="Also create separate menu items import file"
    )
    parser.add_argument(
        "--output-dir",
        default="wp_import",
        help="Output directory for import files (default: wp_import)"
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Find JSON files
    if args.files:
        json_files = args.files
    else:
        # Look for JSON files in scraped_data directory
        scraped_dir = "scraped_data"
        if os.path.exists(scraped_dir):
            json_files = [
                os.path.join(scraped_dir, f) 
                for f in os.listdir(scraped_dir) 
                if f.endswith('.json')
            ]
        else:
            print("Error: No scraped_data directory found. Please specify --files")
            return

    if not json_files:
        print("Error: No JSON files found to convert")
        return

    print(f"Converting {len(json_files)} JSON files...")
    print(f"Output directory: {args.output_dir}")
    print("-" * 50)

    # Convert to CSV format
    csv_file = os.path.join(args.output_dir, "restaurants_import.csv")
    convert_to_csv(json_files, csv_file)
    
    if args.menu_items:
        menu_csv = os.path.join(args.output_dir, "menu_items_import.csv")
        create_menu_items_csv(json_files, menu_csv)

    # Create mapping guide
    guide_file = os.path.join(args.output_dir, "voxel_field_mapping.txt")
    create_voxel_mapping_guide(guide_file)

    print("-" * 50)
    print("✓ Conversion complete!")
    print(f"✓ Files ready for WP All Import in: {args.output_dir}/")
    print("✓ Check voxel_field_mapping.txt for import instructions")


if __name__ == "__main__":
    main() 