# 🚀 Deployment Guide

## Quick Deploy Options

### 1. **Streamlit Community Cloud (FREE & RECOMMENDED)**

**✅ Pros:** Free, easy setup, automatic updates, great for demos
**❌ Cons:** Limited resources, public repos only

**Steps:**
1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/grubhub-scraper.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `scraper_ui.py`
   - Click "Deploy!"

3. **Your app will be live at:**
   `https://yourusername-grubhub-scraper-scraper-ui-xyz123.streamlit.app`

---

### 2. **Railway (FREE TIER)**

**✅ Pros:** Easy deployment, good free tier, supports private repos
**❌ Cons:** Limited free hours per month

**Steps:**
1. **Connect to Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure Environment**
   - Railway will auto-detect Python
   - No additional configuration needed
   - Deployment starts automatically

3. **Custom Domain (Optional)**
   - Go to Settings → Domains
   - Add custom domain or use provided railway.app subdomain

---

### 3. **Render (FREE TIER)**

**✅ Pros:** Good free tier, easy setup, supports static sites too
**❌ Cons:** Can be slower on free tier

**Steps:**
1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name:** grubhub-scraper
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `streamlit run scraper_ui.py --server.port=$PORT --server.address=0.0.0.0`

3. **Deploy**
   - Click "Create Web Service"
   - Deployment starts automatically

---

### 4. **Heroku (PAID - $5/month minimum)**

**✅ Pros:** Reliable, lots of add-ons, good documentation
**❌ Cons:** No longer has free tier

**Steps:**
1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Windows
   # Download from heroku.com/cli
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Add Buildpacks**
   ```bash
   heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-chromedriver
   heroku buildpacks:add --index 2 https://github.com/heroku/heroku-buildpack-google-chrome
   heroku buildpacks:add --index 3 heroku/python
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

---

## 🔧 Environment Configuration

### Required Files (Already Created)

- **`requirements.txt`** - Python dependencies
- **`packages.txt`** - System packages for Streamlit Cloud
- **`Procfile`** - Process configuration for Heroku
- **`runtime.txt`** - Python version specification
- **`.streamlit/config.toml`** - Streamlit configuration

### Environment Variables (Optional)

Set these in your deployment platform if needed:

```bash
# Custom Chrome binary path
CHROME_BINARY_PATH=/usr/bin/chromium-browser

# Custom ChromeDriver path  
CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Custom output directory
SCRAPER_OUTPUT_DIR=./data
```

---

## 🐛 Troubleshooting Deployment

### Common Issues

**1. Chrome/ChromeDriver Not Found**
```
Error: Chrome binary not found
```
**Solution:** The app automatically handles Chrome installation on most platforms. If issues persist, check that `packages.txt` is present.

**2. Memory Issues**
```
Error: Out of memory
```
**Solution:** 
- Reduce parallel workers to 1-2
- Increase timeout values
- Use headless mode (enabled by default)

**3. Timeout Errors**
```
Error: Page load timeout
```
**Solution:**
- Increase timeout in sidebar settings
- Check if the target URLs are accessible
- Try with fewer concurrent requests

**4. Permission Errors**
```
Error: Permission denied
```
**Solution:**
- Ensure all files have proper permissions
- Check if the deployment platform supports file writing

### Platform-Specific Issues

**Streamlit Cloud:**
- Make sure your repo is public
- Check that all files are committed to git
- Verify `packages.txt` is in root directory

**Railway:**
- Check build logs for specific errors
- Ensure environment variables are set correctly
- Verify the start command in railway.toml if needed

**Render:**
- Check that build and start commands are correct
- Verify Python version compatibility
- Monitor resource usage in dashboard

**Heroku:**
- Ensure all buildpacks are added in correct order
- Check dyno logs: `heroku logs --tail`
- Verify Procfile format

---

## 📊 Performance Optimization

### For Production Deployment

1. **Reduce Resource Usage**
   ```python
   # In sidebar settings, set:
   workers = 1  # Start with 1 worker
   timeout = 60  # Increase timeout
   headless = True  # Always use headless mode
   ```

2. **Memory Management**
   - Process restaurants in smaller batches
   - Clear browser cache between requests
   - Use headless mode to reduce memory usage

3. **Rate Limiting**
   - Add delays between requests
   - Respect target website's rate limits
   - Monitor for blocking/captchas

---

## 🔒 Security Considerations

### Data Privacy
- Scraped data is processed in memory
- Files are temporarily stored during export
- No persistent data storage on server

### Legal Compliance
- Ensure compliance with target website's Terms of Service
- Respect robots.txt guidelines
- Use reasonable request rates

### Access Control
- Consider adding authentication for production use
- Monitor usage and resource consumption
- Set up alerts for unusual activity

---

## 🚀 Quick Start Commands

### Local Development
```bash
# Clone and setup
git clone <your-repo>
cd grubhub-scraper
pip install -r requirements.txt

# Run locally
streamlit run scraper_ui.py
```

### Deploy to Streamlit Cloud
```bash
# Push to GitHub
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main

# Then deploy via web interface at share.streamlit.io
```

### Deploy to Railway
```bash
# Connect via Railway dashboard
# Or use Railway CLI
railway login
railway link
railway up
```

---

## 📞 Support

If you encounter deployment issues:

1. **Check the logs** - Most platforms provide detailed deployment logs
2. **Verify dependencies** - Ensure all packages in requirements.txt are available
3. **Test locally first** - Make sure the app works on your machine
4. **Check platform limits** - Free tiers have resource limitations
5. **Review documentation** - Each platform has specific deployment guides

---

**🎉 Once deployed, your scraper will be accessible worldwide!**

Share the URL with others to let them scrape Grubhub restaurant data easily. 