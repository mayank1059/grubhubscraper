# 🍔 Advanced Grubhub Menu Scraper

Professional-grade restaurant data extraction with comprehensive menu analysis and WordPress integration.

## ✨ Features

- **Advanced Web Scraping**: Handles dynamic React content and lazy loading
- **Comprehensive Data Extraction**: Restaurant info, menus, categories, reviews, hours
- **WordPress Integration**: Direct CSV export for WP All Import with Voxel theme
- **Professional UI**: Modern Streamlit interface with real-time progress
- **Multiple Export Formats**: CSV, JSON, WordPress packages
- **Parallel Processing**: Fast scraping with configurable workers
- **Character Encoding**: Proper UTF-8 handling for international characters

## 🚀 Quick Start

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Grubhub-Menu-Scraper-master
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run scraper_ui.py
   ```

4. **Access the interface**
   - Open your browser to `http://localhost:8501`
   - Enter Grubhub restaurant URLs
   - Configure scraping settings
   - Start scraping and export data!

### Online Demo

🌐 **Live Demo**: [Coming Soon - Deploy to Streamlit Cloud]

## 📋 Requirements

- Python 3.8+
- Chrome/Chromium browser
- Internet connection for ChromeDriver auto-download

## 🛠️ Usage

### 1. **Enter Restaurant URLs**
Paste Grubhub restaurant URLs (one per line):
```
https://www.grubhub.com/restaurant/restaurant-name/123456
```

### 2. **Configure Settings**
- **Parallel Workers**: 1-8 (more = faster but higher resource usage)
- **Timeout**: 10-120 seconds per restaurant
- **Headless Mode**: Run browser in background
- **Output Directory**: Where to save scraped data

### 3. **Start Scraping**
Click "Start Scraping" and watch real-time progress with detailed results.

### 4. **Export Data**
Choose from multiple export formats:
- **WordPress CSV**: Ready for WP All Import with Voxel theme
- **JSON Archive**: Raw data in ZIP format
- **Single Restaurant CSV**: Individual restaurant spreadsheet

## 📊 Data Extracted

### Restaurant Information
- Name, address, phone, rating
- Hours (pickup/delivery)
- Cuisines and price range
- Customer reviews
- Delivery information

### Menu Data
- All categories and items
- Names, prices, descriptions
- Item images and IDs
- Complete menu structure

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set custom Chrome binary path
CHROME_BINARY_PATH=/path/to/chrome

# Optional: Set custom output directory
SCRAPER_OUTPUT_DIR=./data
```

### Advanced Settings
- **Max Scroll Attempts**: How many times to scroll for lazy-loaded content
- **Wait Time**: Seconds between page actions
- **Headless Mode**: Browser visibility

## 📁 Project Structure

```
Grubhub-Menu-Scraper-master/
├── scraper_ui.py              # Main Streamlit interface
├── bulk_grubhub_scraper.py    # Core scraping engine
├── wp_import_converter.py     # WordPress integration
├── requirements.txt           # Python dependencies
├── scraped_data/             # Output directory
├── wp_import/                # WordPress CSV exports
└── README.md                 # This file
```

## 🌐 Deployment

### Streamlit Community Cloud (FREE)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy scraper"
   git push origin main
   ```

2. **Deploy on Streamlit**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select `scraper_ui.py` as main file
   - Deploy automatically!

### Railway (FREE TIER)

1. **Connect GitHub repo to Railway**
2. **Add environment variables if needed**
3. **Deploy with one click**

### Heroku

1. **Create Procfile**
2. **Add buildpacks for Chrome**
3. **Deploy via Git**

## ⚠️ Important Notes

### Chrome/ChromeDriver
- ChromeDriver downloads automatically
- For deployment, ensure Chrome is available
- Some platforms may require additional setup

### Rate Limiting
- Be respectful of Grubhub's servers
- Use reasonable delays between requests
- Consider running during off-peak hours

### Legal Compliance
- Ensure compliance with Grubhub's Terms of Service
- Use scraped data responsibly
- Respect robots.txt guidelines

## 🐛 Troubleshooting

### Common Issues

**ChromeDriver Issues**
```bash
# Install Chrome manually if needed
sudo apt-get install google-chrome-stable
```

**Memory Issues**
- Reduce parallel workers
- Increase timeout values
- Use headless mode

**Character Encoding**
- Files use UTF-8 with BOM for Excel compatibility
- All special characters are properly handled

### Error Messages

**"No module named 'selenium'"**
```bash
pip install -r requirements.txt
```

**"ChromeDriver not found"**
- ChromeDriver downloads automatically
- Check internet connection
- Verify Chrome installation

## 📈 Performance Tips

1. **Optimize Workers**: Start with 3 workers, adjust based on performance
2. **Use Headless Mode**: Faster and uses less resources
3. **Reasonable Timeouts**: 45-60 seconds usually sufficient
4. **Batch Processing**: Process restaurants in smaller batches

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please ensure compliance with applicable terms of service and local laws.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review error messages carefully
3. Ensure all dependencies are installed
4. Verify Chrome/ChromeDriver setup

---

**Built with ❤️ using Python, Selenium, and Streamlit** 