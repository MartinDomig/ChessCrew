# Server Deployment Instructions

## Quick Deployment Steps

1. **Pull the latest changes on your server:**
   ```bash
   cd /opt/chesscrew
   git fetch origin
   git checkout claude
   git pull origin claude
   ```

2. **Set up the crawler:**
   ```bash
   cd backend
   chmod +x setup_crawler.sh
   ./setup_crawler.sh
   ```

3. **Debug login (if needed):**
   ```bash
   cd backend
   source venv/bin/activate
   python debug_login.py
   ```

4. **Test the crawler:**
   ```bash
   cd backend
   source venv/bin/activate
   python test_crawler.py
   ```

5. **Set up automatic scheduling:**
   ```bash
   crontab -e
   ```
   Add this line:
   ```
   0 6 * * * /opt/chesscrew/backend/crawler_cron.sh
   ```

## What was added:

### Core Files:
- `backend/chess_results_crawler.py` - Main crawler implementation
- `backend/run_crawler.py` - Script for scheduled execution
- `backend/test_crawler.py` - Test script
- `backend/setup_crawler.sh` - Automated setup script

### Debugging Tools:
- `backend/debug_login.py` - Step-by-step login debugging
- `backend/test_crawler.py` - Full crawler testing  
- `backend/logs/crawler.log` - Application logs

### Login Fixes Applied:
- ✅ Correct login URL (Login.aspx?xx=0)
- ✅ Proper form field detection (PNo and password)
- ✅ ASP.NET viewstate handling
- ✅ Server redirection support
- ✅ Better error detection

## Manual Testing:

After deployment, test manually:

```bash
cd /path/to/chesscrew/backend

# Test individual components (activate venv first)
source venv/bin/activate
python test_crawler.py

# Run full crawler once
python run_crawler.py

# Check logs
tail -f logs/crawler.log
```

## Integration with your app:

The crawler automatically:
1. Logs into chess-results.com with credentials (142838 / zbLiZm58Y)
2. Finds finished Austrian federation tournaments 
3. Skips tournaments without ELO calculation (contain "-" in Elorechnung)
4. Downloads Excel exports from final tables
5. Parses player data and saves to your existing database

## Important Notes:

- The setup script will install required Python packages
- Logs are created in `backend/logs/` directory
- Cron job runs daily at 6 AM by default
- All tournament data integrates with your existing Player/Tournament models
- API endpoints require admin authentication

## Troubleshooting:

If you encounter issues:
1. Check `backend/logs/crawler.log` for detailed logs
2. Activate the virtual environment: `source backend/venv/bin/activate`
3. Run `python test_crawler.py` to diagnose specific problems  
4. Verify network access to chess-results.com from your server
5. Ensure all dependencies are installed correctly in the virtual environment

The crawler is designed to be robust and will skip tournaments it can't process rather than failing completely.
