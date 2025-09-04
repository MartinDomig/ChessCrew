#!/bin/bash
# Chess Results Crawler Setup Script
# This script sets up the automated chess results crawler for daily execution.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Chess Results Crawler Setup${NC}"
echo "================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR"
PROJECT_DIR="$(dirname "$BACKEND_DIR")"

echo "Project directory: $PROJECT_DIR"
echo "Backend directory: $BACKEND_DIR"

# Create logs directory
echo -e "${YELLOW}Creating logs directory...${NC}"
mkdir -p "$BACKEND_DIR/logs"

# Make the crawler executable
echo -e "${YELLOW}Making crawler executable...${NC}"
chmod +x "$BACKEND_DIR/chess_results_crawler.py"
chmod +x "$BACKEND_DIR/test_complete_crawler.py"

# Create a wrapper script for cron
echo -e "${YELLOW}Creating cron wrapper script...${NC}"
cat > "$BACKEND_DIR/run_crawler_cron.sh" << EOF
#!/bin/bash
# Cron wrapper for chess results crawler

# Set up environment
cd "$BACKEND_DIR"
export PYTHONPATH="$BACKEND_DIR:\$PYTHONPATH"

# Activate virtual environment if it exists
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Run the crawler with logging
python3 chess_results_crawler.py >> logs/cron.log 2>&1

# Exit with the same code as the crawler
exit \$?
EOF

chmod +x "$BACKEND_DIR/run_crawler_cron.sh"

# Test the setup
echo -e "${YELLOW}Testing crawler setup...${NC}"
cd "$BACKEND_DIR"

# Test import
if python3 -c "from chess_results_crawler import run_crawler; print('✅ Crawler import successful')" 2>/dev/null; then
    echo -e "${GREEN}✅ Crawler setup successful${NC}"
else
    echo -e "${RED}❌ Crawler import failed${NC}"
    echo "Please check your Python environment and dependencies"
    exit 1
fi

echo ""
echo -e "${GREEN}Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Test the crawler manually:"
echo "   cd $BACKEND_DIR"
echo "   python3 test_complete_crawler.py"
echo ""
echo "2. Set up daily cron job (run as your user):"
echo "   crontab -e"
echo "   Add this line for daily execution at 2 AM:"
echo "   0 2 * * * $BACKEND_DIR/run_crawler_cron.sh"
echo ""
echo "3. Test the cron wrapper:"
echo "   $BACKEND_DIR/run_crawler_cron.sh"
echo ""
echo "4. Monitor logs:"
echo "   tail -f $BACKEND_DIR/logs/crawler.log"
echo "   tail -f $BACKEND_DIR/logs/cron.log"
echo "0 6 * * * $CRON_SCRIPT"
echo ""
echo "You can add it by running:"
echo "crontab -e"
echo ""
echo "Then add the above line to schedule daily crawling."
echo ""
echo "To test the crawler manually, run:"
echo "cd $BACKEND_DIR && source venv/bin/activate && python run_crawler.py"
echo ""
echo "Or use the test script:"
echo "cd $BACKEND_DIR && source venv/bin/activate && python test_crawler.py"
echo ""
echo "Logs will be written to: $BACKEND_DIR/logs/"
