#!/usr/bin/env python3
"""
Advanced Grubhub Menu Scraper
Scrapes restaurant data including business info and categorized menus from Grubhub.
"""

import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
from typing import Dict, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller


def clear_chromedriver_cache():
    """Clear ChromeDriverManager cache to force fresh download."""
    try:
        import shutil
        cache_dir = os.path.expanduser("~/.wdm")
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            print("🗑️ Cleared ChromeDriver cache")
            return True
    except Exception as e:
        print(f"Failed to clear cache: {e}")
    return False


def init_browser(headless: bool = True) -> webdriver.Chrome:
    """Initialize Chrome browser with appropriate settings."""
    options = Options()
    
    if headless:
        options.add_argument("--headless")
    
    # Essential options for Streamlit Cloud
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Don't disable images or JavaScript - needed for Grubhub
    # options.add_argument("--disable-images")  # REMOVED - images needed
    
    # Performance options that don't break functionality
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    
    # Additional options for deployment environments
    options.add_argument("--single-process")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--no-first-run")
    options.add_argument("--safebrowsing-disable-auto-update")
    options.add_argument("--disable-crash-reporter")
    
    # Hide automation indicators
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Window size
    options.add_argument("--window-size=1920,1080")
    
    # Chrome binary path for deployment environments (Debian/Streamlit Cloud)
    chrome_binary = os.environ.get('CHROME_BINARY_PATH')
    if chrome_binary:
        options.binary_location = chrome_binary
        print(f"Using Chrome binary from env: {chrome_binary}")
    elif os.path.exists('/usr/bin/chromium'):
        options.binary_location = '/usr/bin/chromium'
        print("Using Debian Chromium: /usr/bin/chromium")
    elif os.path.exists('/usr/bin/google-chrome-stable'):
        options.binary_location = '/usr/bin/google-chrome-stable'
        print("Using Google Chrome stable")
    elif os.path.exists('/usr/bin/google-chrome'):
        options.binary_location = '/usr/bin/google-chrome'
        print("Using Google Chrome")
    elif os.path.exists('/usr/bin/chromium-browser'):
        options.binary_location = '/usr/bin/chromium-browser'
        print("Using Chromium browser")
    
    # 1) Prefer system-installed driver (chromium-driver package)
    possible_system_drivers = [
        os.environ.get('CHROMEDRIVER_PATH'),            # custom env path
        '/usr/bin/chromedriver',                        # common symlink path
        '/usr/lib/chromium/chromedriver',              # Debian chromium-driver path
        '/usr/local/bin/chromedriver',                 # local install path
    ]
    
    service = None
    for path in possible_system_drivers:
        if path and os.path.exists(path):
            print(f"Using system ChromeDriver: {path}")
            service = Service(path)
            break
    
    # 2) Try chromedriver_autoinstaller if no system driver
    if service is None:
        print("No system driver found, trying chromedriver_autoinstaller...")
        try:
            driver_path = chromedriver_autoinstaller.install()
            if driver_path and os.path.exists(driver_path):
                print(f"chromedriver_autoinstaller installed driver at: {driver_path}")
                service = Service(driver_path)
            else:
                print("chromedriver_autoinstaller failed to provide driver path.")
        except Exception as auto_err:
            print(f"chromedriver_autoinstaller error: {auto_err}")
    
    # 3) Fallback to webdriver_manager (latest)
    if service is None:
        print("Falling back to webdriver_manager latest download...")
        try:
            clear_chromedriver_cache()
            driver_path = ChromeDriverManager(version='LATEST').install()
            service = Service(driver_path)
            print(f"webdriver_manager installed driver at: {driver_path}")
        except Exception as manager_err:
            print(f"webdriver_manager error: {manager_err}")
            # As a last resort try default
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)
            print(f"webdriver_manager default driver at: {driver_path}")
    
    try:
        browser = webdriver.Chrome(service=service, options=options)
        
        # Remove automation indicators
        browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome browser initialized successfully")
        return browser
        
    except Exception as e:
        print(f"❌ Chrome initialization failed: {e}")
        
        # Try to run Chrome setup script as last resort
        try:
            print("🔧 Attempting to install Chrome...")
            import subprocess
            result = subprocess.run([sys.executable, "setup_chrome.py"], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("✅ Chrome installation completed, retrying...")
                # Retry browser initialization
                browser = webdriver.Chrome(service=service, options=options)
                browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                return browser
            else:
                print(f"❌ Chrome installation failed: {result.stderr}")
        except Exception as setup_error:
            print(f"❌ Chrome setup script failed: {setup_error}")
        
        # Final fallback - raise the original error
        raise e


def wait_for_page_load(browser: webdriver.Chrome, timeout: int = 30):
    """Wait for page to load completely."""
    wait = WebDriverWait(browser, timeout)
    
    # Wait for basic page structure
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    
    # Wait for React to load
    time.sleep(3)
    
    # Wait for menu items or menu sections to appear
    try:
        print("Waiting for menu content to load...")
        wait.until(
            lambda driver: driver.find_elements(By.CSS_SELECTOR, "[data-testid='restaurant-menu-item']") or
                          driver.find_elements(By.CSS_SELECTOR, "[data-testid='menuSection-title']")
        )
        print("Menu content detected")
    except:
        print("Menu content not found with primary selectors, waiting longer...")
        time.sleep(5)
    
    # Additional wait for content to stabilize
    time.sleep(3)


def extract_business_info(browser: webdriver.Chrome, soup: BeautifulSoup) -> Dict:
    """Extract business information from the page."""
    business_info = {}
    
    try:
        # Restaurant name
        name_elem = soup.find("h1", {"data-testid": "restaurant-name"})
        if not name_elem:
            name_elem = soup.find("h1")
        if name_elem:
            business_info['name'] = name_elem.get_text(strip=True)
        
        # Address
        address_elem = soup.find(attrs={"data-testid": "restaurant-address"})
        if not address_elem:
            address_elem = soup.find("span", string=re.compile(r"^\s*•.*"))
        if address_elem:
            business_info['address'] = address_elem.get_text(strip=True)
        
        # Phone number - multiple approaches
        phone_elem = soup.find("button", {"data-testid": "restaurant-phone-button"})
        if phone_elem:
            # Extract from button text
            phone_text = phone_elem.get_text(strip=True)
            business_info['phone'] = phone_text
        else:
            # Fallback to tel: link
            phone_elem = soup.find("a", href=re.compile(r"tel:"))
            if phone_elem:
                business_info['phone'] = phone_elem.get_text(strip=True)
        
        # Hours extraction
        hours_info = {}
        
        # Extract pickup hours
        pickup_hours = []
        pickup_elems = soup.find_all(attrs={"data-testid": re.compile("pickupHours\\d+")})
        for elem in pickup_elems:
            hour_text = elem.get_text(strip=True)
            if hour_text and not hour_text.startswith("Pickup:"):
                pickup_hours.append(hour_text)
            elif hour_text.startswith("Pickup:"):
                pickup_hours.append(hour_text.replace("Pickup:", "").strip())
        
        # Extract delivery hours
        delivery_hours = []
        delivery_elems = soup.find_all(attrs={"data-testid": re.compile("deliveryHours\\d+")})
        for elem in delivery_elems:
            hour_text = elem.get_text(strip=True)
            if hour_text and not hour_text.startswith("Delivery:"):
                delivery_hours.append(hour_text)
            elif hour_text.startswith("Delivery:"):
                delivery_hours.append(hour_text.replace("Delivery:", "").strip())
        
        # Combine hours information
        if pickup_hours or delivery_hours:
            if pickup_hours:
                hours_info['pickup'] = " ".join(pickup_hours)
            if delivery_hours:
                hours_info['delivery'] = " ".join(delivery_hours)
            business_info['hours'] = hours_info
        
        # Rating and review count
        rating_elem = soup.find(attrs={"data-testid": re.compile("rating|star")})
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                business_info['rating'] = rating_match.group(1)
        
        # Review count
        review_count_elem = soup.find(string=re.compile(r'\d+\s+review'))
        if review_count_elem:
            count_match = re.search(r'(\d+)', review_count_elem)
            if count_match:
                business_info['review_count'] = count_match.group(1)
        
        # Extract structured address from JSON-LD
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'Restaurant':
                    address = data.get('address', {})
                    if isinstance(address, dict):
                        structured_address = {}
                        if address.get('streetAddress'):
                            structured_address['street'] = address['streetAddress']
                        if address.get('addressLocality'):
                            structured_address['city'] = address['addressLocality']
                        if address.get('addressRegion'):
                            structured_address['state'] = address['addressRegion']
                        if address.get('postalCode'):
                            structured_address['zip'] = address['postalCode']
                        
                        if structured_address:
                            business_info['structured_address'] = structured_address
                    
                    # Phone from JSON-LD (if not already found)
                    if data.get('telephone') and 'phone' not in business_info:
                        business_info['phone'] = data['telephone']
                    
                    # Cuisines/Categories
                    if data.get('servesCuisine'):
                        cuisines = data['servesCuisine']
                        if isinstance(cuisines, list):
                            business_info['cuisines'] = cuisines
                        elif isinstance(cuisines, str):
                            business_info['cuisines'] = [cuisines]
                    
                    # Price range
                    if data.get('priceRange'):
                        business_info['price_range'] = data['priceRange']
                    
                    # Rating from JSON-LD (if not already found)
                    if data.get('aggregateRating') and 'rating' not in business_info:
                        agg_rating = data['aggregateRating']
                        if isinstance(agg_rating, dict):
                            if agg_rating.get('ratingValue'):
                                business_info['rating'] = str(agg_rating['ratingValue'])
                            if agg_rating.get('reviewCount') and 'review_count' not in business_info:
                                business_info['review_count'] = str(agg_rating['reviewCount'])
                        
            except:
                continue
        
        # Extract delivery info
        delivery_info = {}
        
        # Delivery fee
        delivery_fee_elem = soup.find(string=re.compile(r'\$[\d.]+\s+delivery\s+fee', re.I))
        if delivery_fee_elem:
            fee_match = re.search(r'\$[\d.]+', delivery_fee_elem)
            if fee_match:
                delivery_info['delivery_fee'] = fee_match.group()
        
        # Delivery time
        delivery_time_elem = soup.find(string=re.compile(r'\d+[-–]\d+\s+min', re.I))
        if delivery_time_elem:
            time_match = re.search(r'\d+[-–]\d+\s+min', delivery_time_elem, re.I)
            if time_match:
                delivery_info['delivery_time'] = time_match.group()
        
        if delivery_info:
            business_info['delivery_info'] = delivery_info
        
        # Extract reviews (fixed to avoid hours)
        reviews = []
        review_containers = soup.find_all(attrs={"data-testid": "restaurant-review-item"})
        
        for container in review_containers[:10]:  # Limit to first 10 reviews
            try:
                review_data = {}
                
                # Reviewer name
                name_elem = container.find(attrs={"data-testid": "review-reviewer-name"})
                if name_elem:
                    review_data['reviewer_name'] = name_elem.get_text(strip=True)
                
                # Review date
                date_elem = container.find("span", class_=re.compile(".*"))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # Check if it looks like a date (not hours)
                    if re.search(r'\b(ago|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2},?\s*\d{4})', date_text, re.I):
                        review_data['date'] = date_text
                
                # Review text (avoid hours)
                review_text_elem = container.find(attrs={"data-testid": "review-content"})
                if review_text_elem:
                    review_text = review_text_elem.get_text(strip=True)
                    # Filter out hours text
                    if not re.search(r'Pickup:|Delivery:|\d{1,2}:\d{2}\s*(am|pm)', review_text, re.I):
                        review_data['review_text'] = review_text
                
                # Only add review if it has actual review content
                if review_data.get('review_text') and review_data.get('reviewer_name'):
                    reviews.append(review_data)
                    
            except Exception as e:
                continue
        
        if reviews:
            business_info['reviews'] = reviews
            
    except Exception as e:
        print(f"Error extracting business info: {e}")
    
    return business_info


def scroll_to_load_all_items(browser: webdriver.Chrome):
    """Scroll through the page to load all menu items."""
    print("Scrolling to load all menu items...")
    
    # First, try to find the menu container
    menu_container = None
    try:
        # Look for the main menu container
        menu_container = browser.find_element(By.CSS_SELECTOR, "[data-test-id='virtuoso-item-list']")
        print("Found virtualized menu container")
    except:
        try:
            menu_container = browser.find_element(By.CSS_SELECTOR, "div[style*='padding-top'][style*='padding-bottom']")
            print("Found alternative menu container")
        except:
            print("No specific menu container found, will scroll entire page")
    
    last_count = 0
    stable_count = 0
    max_attempts = 30
    
    for attempt in range(max_attempts):
        # Get current count of menu items and categories
        items = browser.find_elements(By.CSS_SELECTOR, "[data-testid='restaurant-menu-item']")
        categories = browser.find_elements(By.CSS_SELECTOR, "[data-testid='menuSection-title']")
        current_count = len(items)
        
        print(f"Scroll attempt {attempt + 1}: Found {len(categories)} categories, {current_count} items")
        
        if current_count == last_count:
            stable_count += 1
            if stable_count >= 3:
                print("Item count stabilized, stopping scroll")
                break
        else:
            stable_count = 0
        
        last_count = current_count
        
        # Multiple scroll strategies
        if menu_container:
            # Scroll within the container
            browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", menu_container)
        else:
            # Scroll the entire page
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(2)
        
        # Also try scrolling up and down to trigger lazy loading
        if attempt % 2 == 0:
            browser.execute_script("window.scrollBy(0, -300);")
            time.sleep(1)
            browser.execute_script("window.scrollBy(0, 600);")
            time.sleep(1)


def extract_menu_from_json_ld(soup: BeautifulSoup) -> Dict[str, List[Dict]]:
    """Extract menu data from JSON-LD structured data."""
    menu_categories = {}
    
    try:
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                
                # Handle different JSON-LD structures
                if isinstance(data, dict):
                    # Look for hasMenu or menu property
                    menu_data = data.get('hasMenu') or data.get('menu')
                    
                    if menu_data and isinstance(menu_data, dict):
                        # Check if hasMenuSection exists
                        sections = menu_data.get('hasMenuSection', [])
                        
                        if isinstance(sections, list):
                            for section in sections:
                                if isinstance(section, dict):
                                    section_name = section.get('name', 'Unknown Category')
                                    
                                    # Get menu items in this section
                                    items = section.get('hasMenuItem', [])
                                    if isinstance(items, list):
                                        category_items = []
                                        
                                        for item in items:
                                            if isinstance(item, dict):
                                                item_data = {
                                                    'name': item.get('name', ''),
                                                    'description': item.get('description', ''),
                                                }
                                                
                                                # Extract price
                                                offers = item.get('offers')
                                                if offers and isinstance(offers, dict):
                                                    price = offers.get('price')
                                                    if price:
                                                        item_data['price'] = f"${price}"
                                                
                                                if item_data['name']:
                                                    category_items.append(item_data)
                                        
                                        if category_items:
                                            menu_categories[section_name] = category_items
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error extracting JSON-LD menu: {e}")
    
    return menu_categories


def extract_menu_from_page_state(browser: webdriver.Chrome) -> Dict[str, List[Dict]]:
    """Try to extract menu data from page's JavaScript state."""
    menu_categories = {}
    
    try:
        # Try to find menu data in window objects
        script = """
        // Look for common menu data patterns in window object
        for (let key in window) {
            if (key.includes('menu') || key.includes('Menu') || key.includes('restaurant')) {
                let val = window[key];
                if (val && typeof val === 'object') {
                    if (val.menu || val.menuSections || val.categories) {
                        return val;
                    }
                }
            }
        }
        
        // Try to find React component data
        let reactElements = document.querySelectorAll('[data-reactroot]');
        for (let elem of reactElements) {
            let keys = Object.keys(elem);
            let reactKey = keys.find(key => key.startsWith('__react'));
            if (reactKey) {
                let reactData = elem[reactKey];
                if (reactData && reactData.memoizedProps) {
                    return reactData.memoizedProps;
                }
            }
        }
        
        return null;
        """
        
        result = browser.execute_script(script)
        
        if result and isinstance(result, dict):
            # Process the found data
            menu_data = result.get('menu') or result.get('menuSections') or result.get('categories')
            
            if menu_data and isinstance(menu_data, list):
                for section in menu_data:
                    if isinstance(section, dict) and section.get('name'):
                        category_name = section['name']
                        items = section.get('items', [])
                        
                        category_items = []
                        for item in items:
                            if isinstance(item, dict) and item.get('name'):
                                item_data = {
                                    'name': item['name'],
                                    'price': item.get('price', ''),
                                    'description': item.get('description', ''),
                                    'id': item.get('id', '')
                                }
                                category_items.append(item_data)
                        
                        if category_items:
                            menu_categories[category_name] = category_items
            
    except Exception as e:
        print(f"Error extracting from page state: {e}")
    
    return menu_categories


def extract_items_then_map_categories(browser: webdriver.Chrome) -> Dict[str, List[Dict]]:
    """Extract menu items and categories together as we scroll through the page."""
    try:
        print("Extracting menu items and categories together...")
        
        menu_categories = {}
        processed_items = set()
        current_category = None
        
        # Scroll to top
        browser.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)
        
        # Progressive scrolling to load everything
        scroll_position = 0
        scroll_increment = 300
        max_scrolls = 100
        
        for scroll_attempt in range(max_scrolls):
            # Scroll down incrementally
            browser.execute_script(f"window.scrollTo(0, {scroll_position})")
            time.sleep(0.5)
            
            # Parse current view
            soup = BeautifulSoup(browser.page_source, "html.parser")
            
            # Find the virtualized list container
            virtualized_list = soup.find("div", {"data-test-id": "virtuoso-item-list"})
            if not virtualized_list:
                virtualized_list = soup.find("div", attrs={"style": re.compile("padding-top.*padding-bottom")})
            
            if virtualized_list:
                # Get all indexed elements (they contain either category headers or items)
                indexed_elements = virtualized_list.find_all("div", {"data-index": True}, recursive=False)
                
                for element in indexed_elements:
                    # Check if this element contains a category header
                    category_header = element.find("h3", {"data-testid": "menuSection-title"})
                    if category_header:
                        # Found a new category
                        new_category = category_header.get_text(strip=True)
                        if new_category:
                            current_category = new_category
                            if current_category not in menu_categories:
                                menu_categories[current_category] = []
                                print(f"  Found category: {current_category}")
                    
                    # Check if this element contains menu items
                    items_container = element.find("div", {"data-testid": "menu-items-container"})
                    if items_container and current_category:
                        # Extract items in this container
                        items = items_container.find_all("article", {"data-testid": "restaurant-menu-item"})
                        
                        for item in items:
                            if 'stencil' not in str(item.get('class', [])):
                                item_data = extract_item_data(item)
                                if item_data and item_data.get('name'):
                                    item_id = item_data.get('id', item_data['name'])
                                    
                                    # Add to current category if not already processed
                                    if item_id not in processed_items:
                                        processed_items.add(item_id)
                                        menu_categories[current_category].append(item_data)
            
            # Also check for any floating items/categories not in virtualized list
            all_categories = soup.find_all("h3", {"data-testid": "menuSection-title"})
            all_items = soup.find_all("article", {"data-testid": "restaurant-menu-item"})
            
            # Process categories and items by their position in DOM
            elements_with_position = []
            
            for cat in all_categories:
                try:
                    # Get position in page
                    parent = cat
                    depth = 0
                    while parent and depth < 10:
                        parent = parent.parent
                        depth += 1
                    elements_with_position.append(('category', cat, cat.get_text(strip=True)))
                except:
                    pass
            
            for item in all_items:
                if 'stencil' not in str(item.get('class', [])):
                    try:
                        item_data = extract_item_data(item)
                        if item_data and item_data.get('name'):
                            elements_with_position.append(('item', item, item_data))
                    except:
                        pass
            
            # Sort by their appearance order in HTML
            # Process in order to maintain category context
            for elem_type, elem, data in elements_with_position:
                if elem_type == 'category':
                    current_category = data
                    if current_category not in menu_categories:
                        menu_categories[current_category] = []
                elif elem_type == 'item' and current_category:
                    item_id = data.get('id', data['name'])
                    if item_id not in processed_items:
                        processed_items.add(item_id)
                        if current_category in menu_categories:
                            # Check if item already exists in category
                            if not any(existing['name'] == data['name'] for existing in menu_categories[current_category]):
                                menu_categories[current_category].append(data)
            
            # Status update
            total_items = sum(len(items) for items in menu_categories.values())
            print(f"  Scroll {scroll_attempt + 1}: {len(menu_categories)} categories, {total_items} items")
            
            # Update scroll position
            scroll_position += scroll_increment
            
            # Check if we've reached the bottom
            new_height = browser.execute_script("return document.body.scrollHeight")
            if scroll_position >= new_height:
                # Scroll to absolute bottom
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                
                # Final check
                final_height = browser.execute_script("return document.body.scrollHeight")
                if final_height == new_height:
                    print("  Reached bottom of page")
                    break
        
        # Remove empty categories
        menu_categories = {k: v for k, v in menu_categories.items() if v}
        
        # Summary
        total_items = sum(len(items) for items in menu_categories.values())
        print(f"\n✓ Extracted {len(menu_categories)} categories with {total_items} total items:")
        for cat, items in menu_categories.items():
            print(f"  - {cat}: {len(items)} items")
        
        return menu_categories
        
    except Exception as e:
        print(f"✗ Error in combined extraction: {e}")
        import traceback
        traceback.print_exc()
        return {}


def extract_menu_categories(browser: webdriver.Chrome, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
    """Extract menu data maintaining category structure."""
    # Use combined approach - extract all items first, then categories, then map them
    print("Using combined extraction approach...")
    menu_categories = extract_items_then_map_categories(browser)
    
    if menu_categories:
        return menu_categories
    
    # Try to get menu from page's JavaScript state
    print("Trying to extract menu from page state...")
    menu_categories = extract_menu_from_page_state(browser)
    
    if menu_categories:
        return menu_categories
    
    # Then try JSON-LD
    print("Trying to extract menu from JSON-LD...")
    menu_categories = extract_menu_from_json_ld(soup)
    
    if menu_categories:
        print(f"Successfully extracted {len(menu_categories)} categories from JSON-LD")
        return menu_categories
    
    # Final fallback
    print("Using fallback DOM extraction...")
    menu_categories = {}
    
    # Find the virtualized item list container
    item_list = soup.find("div", {"data-test-id": "virtuoso-item-list"})
    if not item_list:
        # Try alternative selectors
        item_list = soup.find("div", attrs={"style": re.compile("padding-top.*padding-bottom")})
    
    if item_list:
        print("Found virtualized list container")
        
        # Get all child divs which contain either sections or items
        children = item_list.find_all("div", {"data-index": True}, recursive=False)
        print(f"Found {len(children)} indexed elements in virtualized list")
        
        current_category = None
        menu_categories = {}
        
        for i, child in enumerate(children):
            # Check if this is a section header
            section_elem = child.find("div", {"id": re.compile("menuSection\\d+")})
            if section_elem:
                # Extract category name
                title_elem = section_elem.find("h3", {"data-testid": "menuSection-title"})
                if not title_elem:
                    title_elem = section_elem.find("h3")
                
                if title_elem:
                    current_category = title_elem.get_text(strip=True)
                    if current_category not in menu_categories:
                        menu_categories[current_category] = []
                    print(f"  Found category: {current_category}")
            
            # Check if this contains menu items
            items_container = child.find("div", {"data-testid": "menu-items-container"})
            if items_container and current_category:
                # Extract items from this container
                menu_items = items_container.find_all("article", {"data-testid": "restaurant-menu-item"})
                
                for item in menu_items:
                    # Skip stencil/placeholder items
                    if 'stencil' in str(item.get('class', [])):
                        continue
                        
                    item_data = extract_item_data(item)
                    if item_data and item_data.get('name'):
                        # Check if item already exists (avoid duplicates)
                        if not any(existing['name'] == item_data['name'] for existing in menu_categories[current_category]):
                            menu_categories[current_category].append(item_data)
        
        # Remove empty categories
        menu_categories = {k: v for k, v in menu_categories.items() if v}
        
        # Summary
        for category, items in menu_categories.items():
            print(f"  Category '{category}': {len(items)} items")
    
    return menu_categories


def extract_item_data(item) -> Dict:
    """Extract data from a single menu item element."""
    item_data = {}
    
    # Name
    name_elem = item.find("h6", {"data-testid": True})
    if not name_elem:
        name_elem = item.find("h6")
    
    if name_elem:
        item_data['name'] = name_elem.get_text(strip=True)
    else:
        return {}
    
    # Price
    price_elem = item.find(attrs={"data-testid": "menu-item-price"})
    if not price_elem:
        price_elem = item.find("span", {"itemprop": "price"})
    if not price_elem:
        price_elem = item.find(string=re.compile(r"\$[\d,]+\.?\d*"))
        if price_elem:
            price_elem = price_elem.parent
    
    if price_elem and hasattr(price_elem, 'get_text'):
        price_text = price_elem.get_text(strip=True)
        if not price_text.startswith('$'):
            price_match = re.search(r'\$[\d,]+\.?\d*\+?', price_text)
            if price_match:
                price_text = price_match.group()
        item_data['price'] = price_text
    
    # Description
    desc_elem = item.find(attrs={"data-testid": "menu-item-description"})
    if not desc_elem:
        desc_elem = item.find("span", class_=re.compile("description", re.I))
    
    if desc_elem:
        item_data['description'] = desc_elem.get_text(strip=True)
    
    # Image URL
    img_elem = item.find("img", {"alt": True})
    if img_elem and img_elem.get("src"):
        src = img_elem["src"]
        if not src.startswith("data:image") and "lazy" not in src:
            item_data['image_url'] = src
    
    # Item ID (useful for tracking)
    parent_div = item.find_parent("div", {"id": re.compile("Item\\d+")})
    if parent_div:
        item_data['id'] = parent_div.get('id')
    
    return item_data


def scrape_restaurant_data(url: str, headless: bool = True, timeout: int = 30) -> Dict:
    """Scrape complete restaurant data including business info and categorized menu."""
    browser = None
    try:
        browser = init_browser(headless=headless)
        print(f"Loading {url}...")
        browser.get(url)
        
        wait_for_page_load(browser, timeout)
        
        # Scroll to load all items
        scroll_to_load_all_items(browser)
        
        # Wait for final render
        time.sleep(2)
        
        # Parse the page
        soup = BeautifulSoup(browser.page_source, "html.parser")
        
        # Extract business information
        print("Extracting business information...")
        business_info = extract_business_info(browser, soup)
        
        # Extract menu with categories
        print("Extracting menu categories...")
        menu_categories = extract_menu_categories(browser, soup)
        
        # Combine all data
        restaurant_data = {
            'restaurant_info': business_info,
            'menu': menu_categories,
            'url': url,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Summary
        total_items = sum(len(items) for items in menu_categories.values())
        print(f"\nSummary:")
        print(f"  Restaurant: {business_info.get('name', 'Unknown')}")
        print(f"  Categories: {len(menu_categories)}")
        print(f"  Total items: {total_items}")
        
        if not menu_categories:
            print(f"Warning: No menu items found for {url}")
            # Save page source for debugging
            debug_file = f"debug_{url.split('/')[-1]}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(browser.page_source)
            print(f"Saved page source to {debug_file} for inspection")
        
        return restaurant_data
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        raise
    finally:
        if browser:
            browser.quit()


def save_restaurant_data(output_dir: str, url: str, data: Dict):
    """Save the restaurant data to a JSON file."""
    # Extract restaurant name from URL
    match = re.search(r'/restaurant/([^/]+)/\d+', url)
    if match:
        slug = match.group(1)
    else:
        slug = url.rstrip("/").split("/")[-1] or "restaurant"
    
    filename = f"{slug}_data.json"
    path = os.path.join(output_dir, filename)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    restaurant_name = data.get('restaurant_info', {}).get('name', 'Unknown')
    categories = len(data.get('menu', {}))
    total_items = sum(len(items) for items in data.get('menu', {}).values())
    
    print(f"[✓] Saved {filename}")
    print(f"    Restaurant: {restaurant_name}")
    print(f"    Categories: {categories}, Items: {total_items}")


def worker(url: str, output_dir: str, headless: bool, timeout: int):
    """Worker function for parallel processing."""
    try:
        data = scrape_restaurant_data(url, headless=headless, timeout=timeout)
        if data and data.get('menu'):
            save_restaurant_data(output_dir, url, data)
        else:
            print(f"[!] No data found for {url}")
    except Exception as exc:
        print(f"[✗] Failed to scrape {url}: {exc}")


def main():
    parser = argparse.ArgumentParser(
        description="Bulk scrape Grubhub restaurant data including business info and categorized menus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a single URL
  python bulk_grubhub_scraper.py -u https://www.grubhub.com/restaurant/example/12345
  
  # Scrape URLs from a file
  python bulk_grubhub_scraper.py urls.txt
  
  # Scrape with visible browser (debugging)
  python bulk_grubhub_scraper.py urls.txt --no-headless
  
  # Use more workers for faster processing
  python bulk_grubhub_scraper.py urls.txt --workers 4
        """
    )
    
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a text file containing Grubhub restaurant URLs (one per line).",
    )
    parser.add_argument(
        "-u", "--url",
        help="Single URL to scrape (alternative to input file)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="scraped_data",
        help="Directory to store scraped JSON files (default: scraped_data).",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run Chrome in visible mode (useful for debugging).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel browser workers (default: 1).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Seconds to wait for page elements (default: 30).",
    )

    args = parser.parse_args()

    # Determine URLs to process
    urls = []
    
    if args.url:
        urls = [args.url]
    elif args.input:
        if not os.path.isfile(args.input):
            print(f"Error: Input file '{args.input}' not found.")
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        parser.print_help()
        sys.exit(1)

    if not urls:
        print("Error: No URLs provided.")
        sys.exit(1)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Scraping {len(urls)} URL(s)...")
    print(f"Output directory: {args.output_dir}")
    print(f"Workers: {args.workers}")
    print(f"Headless: {not args.no_headless}")
    print("-" * 50)
    
    start_time = time.time()
    
    if args.workers == 1 or len(urls) == 1:
        # Sequential processing
        for url in urls:
            worker(url, args.output_dir, not args.no_headless, args.timeout)
    else:
        # Parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(worker, url, args.output_dir, not args.no_headless, args.timeout)
                for url in urls
            ]
            concurrent.futures.wait(futures)
    
    elapsed = time.time() - start_time
    print("-" * 50)
    print(f"[Finished] Completed in {elapsed:.1f} seconds")


if __name__ == "__main__":
    main() 