import concurrent.futures
import pathlib
import textwrap
from typing import List, Dict, Any
import json
import os
import time
from datetime import datetime
import zipfile
import tempfile
import io

import streamlit as st

# Ensure bulk_grubhub_scraper is in path
import sys
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bulk_grubhub_scraper as scraper

def clean_text_for_export(text: str) -> str:
    """Clean text for export - fix encoding issues."""
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
    import re
    text = re.sub(r'\r\n|\r|\n', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove leading bullet point if present (e.g., "• 215 E Liberty St" or "•215 E Liberty St")
    if text.startswith('•'):
        text = text.lstrip('•').strip()
    
    return text

# Page config
st.set_page_config(
    page_title="Advanced Grubhub Menu Scraper",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling and text visibility
st.markdown("""
<style>
    /* FORCE DARK TEXT EVERYWHERE - NUCLEAR OPTION */
    * {
        color: #000000 !important;
    }
    
    /* Force all text to be dark on white background */
    .main .block-container {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Override Streamlit's default styling */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #ff6b35, #f7931e);
        padding: 2rem;
        border-radius: 10px;
        color: white !important;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        color: white !important;
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
    }
    
    /* Metric cards with high contrast */
    .metric-card {
        background: #f8f9fa !important;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
        text-align: center;
    }
    
    .metric-card h4 {
        color: #495057 !important;
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }
    
    .metric-card h2 {
        color: #ff6b35 !important;
        margin: 0.5rem 0;
        font-weight: bold;
        font-size: 2rem;
    }
    
    .metric-card p {
        color: #6c757d !important;
        margin: 0;
        font-size: 0.9rem;
    }
    
    /* Success cards */
    .success-card {
        background: #d1f2eb !important;
        border: 2px solid #a3e4d7;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .success-card h4 {
        color: #0e6b47 !important;
        margin: 0 0 0.5rem 0;
        font-weight: bold;
    }
    
    .success-card p {
        color: #0e6b47 !important;
        margin: 0.25rem 0;
    }
    
    .success-card strong {
        color: #0e6b47 !important;
    }
    
    /* Error cards */
    .error-card {
        background: #fadbd8 !important;
        border: 2px solid #f5b7b1;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .error-card h4 {
        color: #922b21 !important;
        margin: 0 0 0.5rem 0;
        font-weight: bold;
    }
    
    .error-card p {
        color: #922b21 !important;
        margin: 0.25rem 0;
    }
    
    .error-card strong {
        color: #922b21 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #ff6b35, #f7931e) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #e55a2b, #e6841a) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Force dark text everywhere - AGGRESSIVE */
    .stMarkdown, .stMarkdown *, .stText, .stText *, 
    p, div, span, label, h1, h2, h3, h4, h5, h6,
    .css-1d391kg, .css-1d391kg *, 
    [data-testid="stSidebar"], [data-testid="stSidebar"] *,
    .main, .main *, .block-container, .block-container * {
        color: #000000 !important;
    }
    
    /* Sidebar text - FORCE BLACK */
    .css-1d391kg * {
        color: #000000 !important;
    }
    
    /* Input fields - FORCE BLACK TEXT */
    .stTextInput > div > div > input {
        color: #000000 !important;
        background-color: white !important;
        border: 2px solid #dee2e6 !important;
    }
    
    .stTextArea > div > div > textarea {
        color: #000000 !important;
        background-color: white !important;
        border: 2px solid #dee2e6 !important;
    }
    
    .stSelectbox > div > div > select {
        color: #000000 !important;
        background-color: white !important;
    }
    
    /* FORCE ALL INPUT LABELS TO BE BLACK */
    label, .stSelectbox label, .stTextInput label, .stTextArea label {
        color: #000000 !important;
    }
    
    /* Alert messages - FORCE BLACK */
    .stAlert > div {
        color: #000000 !important;
    }
    
    .stSuccess > div {
        color: #0e6b47 !important;
        background-color: #d1f2eb !important;
    }
    
    .stError > div {
        color: #922b21 !important;
        background-color: #fadbd8 !important;
    }
    
    .stWarning > div {
        color: #b7950b !important;
        background-color: #fcf3cf !important;
    }
    
    .stInfo > div {
        color: #1b4f72 !important;
        background-color: #d6eaf8 !important;
    }
    
    /* Expander styling - FORCE BLACK */
    .streamlit-expanderHeader {
        color: #000000 !important;
        background-color: #f8f9fa !important;
    }
    
    .streamlit-expanderContent {
        color: #000000 !important;
        background-color: white !important;
    }
    
    /* NUCLEAR OPTION - FORCE EVERYTHING BLACK */
    body, body *, html, html *, 
    .stApp, .stApp *, 
    .main, .main *, 
    .block-container, .block-container *,
    div, div *, span, span *, p, p *, 
    h1, h1 *, h2, h2 *, h3, h3 *, h4, h4 *, h5, h5 *, h6, h6 *,
    label, label *, 
    .stMarkdown, .stMarkdown *,
    .stText, .stText *,
    .css-1d391kg, .css-1d391kg * {
        color: #000000 !important;
    }
    
    /* Exceptions for elements that should stay white text */
    .main-header *, 
    .stButton > button * {
        color: white !important;
    }
    
    /* Form labels for both themes */
    [data-theme="light"] .stSelectbox label, 
    [data-theme="light"] .stTextInput label, 
    [data-theme="light"] .stTextArea label, 
    [data-theme="light"] .stSlider label {
        color: #333 !important;
    }
    
    [data-theme="dark"] .stSelectbox label, 
    [data-theme="dark"] .stTextInput label, 
    [data-theme="dark"] .stTextArea label, 
    [data-theme="dark"] .stSlider label {
        color: #fff !important;
    }
    
    /* Metrics for both themes */
    [data-theme="light"] .stMetric label {
        color: #666 !important;
    }
    [data-theme="light"] .stMetric [data-testid="metric-value"] {
        color: #333 !important;
    }
    
    [data-theme="dark"] .stMetric label {
        color: #ccc !important;
    }
    [data-theme="dark"] .stMetric [data-testid="metric-value"] {
        color: #fff !important;
    }
    
    /* Fallback for when theme detection doesn't work */
    .stApp {
        color: var(--text-color, #333);
    }
    
    /* Alternative approach - use CSS variables that adapt to theme */
    :root {
        --text-color: #333;
        --muted-text-color: #666;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #fff;
            --muted-text-color: #ccc;
        }
    }
    
    /* Apply adaptive colors */
    .stMarkdown, .stText, p, div, span, label {
        color: var(--text-color) !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color) !important;
    }
    .stSelectbox label, .stTextInput label, .stTextArea label, .stSlider label {
        color: var(--text-color) !important;
    }
    .stMetric label {
        color: var(--muted-text-color) !important;
    }
    .stMetric [data-testid="metric-value"] {
        color: var(--text-color) !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🍔 Advanced Grubhub Menu Scraper</h1>
    <p>Professional-grade restaurant data extraction with comprehensive menu analysis</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Scraping settings
    st.subheader("Scraping Settings")
    workers = st.slider("Parallel Workers", min_value=1, max_value=8, value=3, 
                       help="More workers = faster scraping, but higher resource usage")
    timeout = st.slider("Timeout (seconds)", min_value=10, max_value=120, value=45,
                       help="How long to wait for each restaurant page to load")
    headless = st.checkbox("Headless Mode", value=True, 
                          help="Run browser in background (recommended)")
    
    # Output settings
    st.subheader("Output Settings")
    output_dir = st.text_input("Output Directory", value="scraped_data",
                              help="Where to save the scraped data files")
    
    # Advanced options
    st.subheader("Advanced Options")
    max_scroll_attempts = st.slider("Max Scroll Attempts", min_value=5, max_value=20, value=10,
                                   help="How many times to scroll to load all menu items")
    wait_time = st.slider("Wait Time Between Actions", min_value=1.0, max_value=5.0, value=2.0, step=0.5,
                         help="Seconds to wait between page actions")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("🎯 Restaurant URLs")
    st.markdown("Enter Grubhub restaurant URLs (one per line)")
    
    # Sample URLs for demo
    sample_urls = """https://www.grubhub.com/restaurant/rallys-4154-lee-rd-cleveland/2007838
https://www.grubhub.com/restaurant/mcdonalds-123-main-st/1234567
https://www.grubhub.com/restaurant/burger-king-456-oak-ave/7654321"""
    
    urls_input = st.text_area(
        "Restaurant URLs",
        height=150,
        placeholder="Paste Grubhub restaurant URLs here...\n\nExample:\n" + sample_urls,
        help="Each URL should be on a separate line"
    )
    
    # URL validation
    if urls_input:
        urls = [u.strip() for u in urls_input.splitlines() if u.strip()]
        valid_urls = [url for url in urls if 'grubhub.com/restaurant/' in url]
        invalid_urls = [url for url in urls if url not in valid_urls]
        
        if invalid_urls:
            st.warning(f"⚠️ {len(invalid_urls)} invalid URL(s) detected. Only Grubhub restaurant URLs are supported.")
            with st.expander("Show invalid URLs"):
                for url in invalid_urls:
                    st.text(f"❌ {url}")
        
        if valid_urls:
            st.success(f"✅ {len(valid_urls)} valid URL(s) ready for scraping")

with col2:
    st.header("📊 Quick Stats")
    
    # Display current scraped data stats
    if os.path.exists(output_dir):
        json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        if json_files:
            st.markdown(f"""
            <div class="metric-card">
                <h4>📁 Scraped Restaurants</h4>
                <h2>{len(json_files)}</h2>
                <p>Total restaurants in database</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Load and analyze existing data
            total_menu_items = 0
            total_categories = 0
            restaurants_data = []
            
            for json_file in json_files[:5]:  # Limit to 5 for performance
                try:
                    with open(os.path.join(output_dir, json_file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        menu = data.get('menu', {})
                        total_categories += len(menu)
                        total_menu_items += sum(len(items) for items in menu.values())
                        restaurants_data.append({
                            'name': data.get('restaurant_info', {}).get('name', 'Unknown'),
                            'categories': len(menu),
                            'items': sum(len(items) for items in menu.values()),
                            'rating': data.get('restaurant_info', {}).get('rating', 'N/A')
                        })
                except:
                    continue
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>🍽️ Menu Items</h4>
                <h2>{total_menu_items}</h2>
                <p>Across {total_categories} categories</p>
            </div>
            """, unsafe_allow_html=True)
            
            if restaurants_data:
                st.subheader("Recent Restaurants")
                for restaurant in restaurants_data:
                    st.markdown(f"""
                    **{clean_text_for_export(restaurant['name'])}**  
                    📊 {restaurant['categories']} categories, {restaurant['items']} items  
                    ⭐ Rating: {restaurant['rating']}
                    """)
        else:
            st.info("No scraped data found. Start scraping to see statistics!")
    else:
        st.info("Output directory doesn't exist yet. It will be created when you start scraping.")

# Scraping section
st.header("🚀 Start Scraping")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    scrape_button = st.button("🔥 Start Scraping", type="primary", use_container_width=True)

with col2:
    if st.button("📂 View Results", use_container_width=True):
        st.session_state.show_results = True

with col3:
    if st.button("📤 Export Data", use_container_width=True):
        st.session_state.show_export = True

# Scraping logic
if scrape_button:
    urls = [u.strip() for u in urls_input.splitlines() if u.strip() and 'grubhub.com/restaurant/' in u]
    
    if not urls:
        st.error("❌ Please add at least one valid Grubhub restaurant URL.")
    else:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize session state for real-time updates
        if 'scraping_results' not in st.session_state:
            st.session_state.scraping_results = []
        
        st.session_state.scraping_results = []
        
        # Progress tracking
        progress_container = st.container()
        with progress_container:
            st.subheader("🔄 Scraping Progress")
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
        
        def run_scraping_task(url, index):
            """Enhanced scraping task with detailed progress"""
            try:
                start_time = time.time()
                
                # Update status
                status_text.text(f"🔄 Scraping restaurant {index + 1}/{len(urls)}: {url}")
                
                # Run the scraper
                restaurant_data = scraper.scrape_restaurant_data(
                    url, 
                    headless=headless, 
                    timeout=timeout
                )
                
                # Save data
                filename = scraper.save_restaurant_data(output_dir, url, restaurant_data)
                
                end_time = time.time()
                duration = round(end_time - start_time, 2)
                
                # Extract key metrics
                restaurant_info = restaurant_data.get('restaurant_info', {})
                menu = restaurant_data.get('menu', {})
                
                result = {
                    'url': url,
                    'success': True,
                    'filename': filename,
                    'duration': duration,
                    'restaurant_name': restaurant_info.get('name', 'Unknown'),
                    'categories': len(menu),
                    'menu_items': sum(len(items) for items in menu.values()),
                    'rating': restaurant_info.get('rating', 'N/A'),
                    'phone': restaurant_info.get('phone', 'N/A'),
                    'address': restaurant_info.get('address', 'N/A'),
                    'error': None
                }
                
                return result
                
            except Exception as exc:
                end_time = time.time()
                duration = round(end_time - start_time, 2)
                
                return {
                    'url': url,
                    'success': False,
                    'filename': None,
                    'duration': duration,
                    'restaurant_name': 'Failed',
                    'categories': 0,
                    'menu_items': 0,
                    'rating': 'N/A',
                    'phone': 'N/A',
                    'address': 'N/A',
                    'error': str(exc)
                }
        
        # Execute scraping
        total_urls = len(urls)
        completed = 0
        
        # Sequential execution for better progress tracking
        for i, url in enumerate(urls):
            result = run_scraping_task(url, i)
            st.session_state.scraping_results.append(result)
            
            completed += 1
            progress_bar.progress(completed / total_urls)
            
            # Display result immediately
            with results_container:
                if result['success']:
                    st.markdown(f"""
                    <div class="success-card">
                        <h4>✅ {clean_text_for_export(result['restaurant_name'])}</h4>
                        <p><strong>File:</strong> {result['filename']}</p>
                        <p><strong>Menu:</strong> {result['categories']} categories, {result['menu_items']} items</p>
                        <p><strong>Rating:</strong> {result['rating']} | <strong>Duration:</strong> {result['duration']}s</p>
                        <p><strong>Address:</strong> {clean_text_for_export(result['address'])}</p>
                        <p><strong>Phone:</strong> {clean_text_for_export(result['phone'])}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="error-card">
                        <h4>❌ Failed: {result['url']}</h4>
                        <p><strong>Error:</strong> {result['error']}</p>
                        <p><strong>Duration:</strong> {result['duration']}s</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Final summary
        successful = sum(1 for r in st.session_state.scraping_results if r['success'])
        failed = total_urls - successful
        total_items = sum(r['menu_items'] for r in st.session_state.scraping_results if r['success'])
        total_categories = sum(r['categories'] for r in st.session_state.scraping_results if r['success'])
        
        status_text.text("🎉 Scraping completed!")
        
        st.success(f"""
        ## 🎉 Scraping Complete!
        
        **Summary:**
        - ✅ **Successful:** {successful} restaurants
        - ❌ **Failed:** {failed} restaurants
        - 📊 **Total Menu Items:** {total_items}
        - 🏷️ **Total Categories:** {total_categories}
        - 📁 **Files saved in:** `{output_dir}/`
        """)

# Results viewer
if st.session_state.get('show_results', False):
    st.header("📊 Scraped Data Results")
    
    if os.path.exists(output_dir):
        json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
        
        if json_files:
            selected_file = st.selectbox("Select a restaurant file to view:", json_files)
            
            if selected_file:
                file_path = os.path.join(output_dir, selected_file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    restaurant_info = data.get('restaurant_info', {})
                    menu = data.get('menu', {})
                    
                    # Restaurant overview
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Restaurant", clean_text_for_export(restaurant_info.get('name', 'Unknown')))
                        st.metric("Rating", restaurant_info.get('rating', 'N/A'))
                    
                    with col2:
                        st.metric("Menu Categories", len(menu))
                        st.metric("Total Items", sum(len(items) for items in menu.values()))
                    
                    with col3:
                        st.metric("Phone", clean_text_for_export(restaurant_info.get('phone', 'N/A')))
                        st.metric("Price Range", restaurant_info.get('price_range', 'N/A'))
                    
                    # Menu breakdown
                    st.subheader("📋 Menu Categories")
                    
                    for category, items in menu.items():
                        with st.expander(f"{category} ({len(items)} items)"):
                            for item in items[:5]:  # Show first 5 items
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"**{clean_text_for_export(item.get('name', 'Unknown'))}**")
                                    if item.get('description'):
                                        desc = clean_text_for_export(item.get('description', ''))
                                        st.write(desc[:100] + "..." if len(desc) > 100 else desc)
                                with col2:
                                    st.write(f"**{clean_text_for_export(item.get('price', 'N/A'))}**")
                            
                            if len(items) > 5:
                                st.write(f"... and {len(items) - 5} more items")
                    
                    # Raw JSON viewer
                    with st.expander("🔍 View Raw JSON Data"):
                        st.json(data)
                        
                except Exception as e:
                    st.error(f"Error loading file: {e}")
        else:
            st.info("No scraped data files found. Start scraping to see results!")
    else:
        st.info("Output directory doesn't exist. Start scraping to create data!")

# Export functionality
if st.session_state.get('show_export', False):
    st.header("📤 Export Data")
    
    export_format = st.selectbox("Choose export format:", 
                                ["CSV for WordPress (WP All Import)", "Raw JSON Archive", "Single Restaurant CSV"])
    
    if st.button("Generate Export"):
        if export_format == "CSV for WordPress (WP All Import)":
            # Run the WP converter
            try:
                import wp_import_converter
                
                # Find JSON files
                if os.path.exists(output_dir):
                    json_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.json')]
                    
                    if json_files:
                        with st.spinner("Creating WordPress import files..."):
                            # Create temporary directory for files
                            with tempfile.TemporaryDirectory() as temp_dir:
                                # Convert to CSV
                                restaurants_csv = os.path.join(temp_dir, "restaurants_import.csv")
                                menu_csv = os.path.join(temp_dir, "menu_items_import.csv")
                                guide_file = os.path.join(temp_dir, "voxel_field_mapping.txt")
                                
                                wp_import_converter.convert_to_csv(json_files, restaurants_csv)
                                wp_import_converter.create_menu_items_csv(json_files, menu_csv)
                                wp_import_converter.create_voxel_mapping_guide(guide_file)
                                
                                # Create ZIP file in memory
                                zip_buffer = io.BytesIO()
                                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                    zip_file.write(restaurants_csv, "restaurants_import.csv")
                                    zip_file.write(menu_csv, "menu_items_import.csv")
                                    zip_file.write(guide_file, "voxel_field_mapping.txt")
                                
                                zip_buffer.seek(0)
                                
                                # Create download button
                                st.success("✅ **WordPress Import Package Ready!**")
                                st.download_button(
                                    label="📦 Download WordPress Import ZIP",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"grubhub_wordpress_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                    mime="application/zip",
                                    help="Contains: restaurants_import.csv, menu_items_import.csv, and setup guide"
                                )
                                
                                st.info("""
                                **Package Contents:**
                                - `restaurants_import.csv` - Restaurant data for WP All Import
                                - `menu_items_import.csv` - Individual menu items  
                                - `voxel_field_mapping.txt` - Complete setup instructions
                                """)
                    else:
                        st.error("No data files found to export!")
                else:
                    st.error("No scraped data directory found!")
                    
            except ImportError:
                st.error("WordPress converter not available. Please check wp_import_converter.py file.")
        
        elif export_format == "Raw JSON Archive":
            if os.path.exists(output_dir):
                json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
                
                if json_files:
                    with st.spinner("Creating JSON archive..."):
                        # Create ZIP file in memory
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for json_file in json_files:
                                file_path = os.path.join(output_dir, json_file)
                                zip_file.write(file_path, json_file)
                        
                        zip_buffer.seek(0)
                        
                        st.success("✅ **JSON Archive Ready!**")
                        st.download_button(
                            label="📦 Download JSON Archive",
                            data=zip_buffer.getvalue(),
                            file_name=f"grubhub_raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            help=f"Contains {len(json_files)} restaurant JSON files"
                        )
                else:
                    st.error("No JSON files found to export!")
            else:
                st.error("No scraped data directory found!")
        
        elif export_format == "Single Restaurant CSV":
            if os.path.exists(output_dir):
                json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
                
                if json_files:
                    selected_restaurant = st.selectbox("Select restaurant to export:", json_files)
                    
                    if st.button("Export Selected Restaurant"):
                        with st.spinner("Creating CSV file..."):
                            try:
                                # Load the selected restaurant data
                                with open(os.path.join(output_dir, selected_restaurant), 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                
                                restaurant_info = data.get('restaurant_info', {})
                                menu = data.get('menu', {})
                                
                                # Create CSV data with cleaned text
                                csv_data = []
                                for category, items in menu.items():
                                    for item in items:
                                        csv_data.append({
                                            'Restaurant': clean_text_for_export(restaurant_info.get('name', 'Unknown')),
                                            'Category': clean_text_for_export(category),
                                            'Item Name': clean_text_for_export(item.get('name', '')),
                                            'Price': clean_text_for_export(item.get('price', '')),
                                            'Description': clean_text_for_export(item.get('description', '')),
                                            'Image URL': item.get('image_url', ''),
                                            'Item ID': item.get('id', '')
                                        })
                                
                                # Convert to CSV with proper encoding
                                import pandas as pd
                                df = pd.DataFrame(csv_data)
                                # Use BytesIO and utf-8-sig to include BOM so Excel reads UTF-8 correctly
                                csv_buffer = io.BytesIO()
                                df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                                csv_buffer.seek(0)
                                
                                st.success("✅ **Restaurant CSV Ready!**")
                                st.download_button(
                                    label="📄 Download Restaurant CSV",
                                    data=csv_buffer.getvalue(),
                                    file_name=f"{restaurant_info.get('name', 'restaurant').replace(' ', '_').lower()}_menu.csv",
                                    mime="text/csv",
                                    help="Menu items in spreadsheet format"
                                )
                                
                                # Show preview
                                st.subheader("📊 Preview")
                                st.dataframe(df.head(10))
                                
                            except Exception as e:
                                st.error(f"Error creating CSV: {e}")
                else:
                    st.error("No restaurants found to export!")
            else:
                st.error("No scraped data directory found!")
        
        

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🍔 <strong>Advanced Grubhub Menu Scraper</strong> | Built with Streamlit & Selenium</p>
    <p>Extract comprehensive restaurant data including menus, reviews, and business information</p>
</div>
""", unsafe_allow_html=True) 