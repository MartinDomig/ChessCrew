# Chess Crew Test Suite

This directory contains test scripts for the Chess Crew tournament management system.

## Test Scripts Overview

### Main Test Runners

#### `./run_all_tests.sh`
**Comprehensive test suite runner**
- Runs all available tests in the system
- Provides detailed output with colored formatting
- Generates summary report with pass/fail counts
- Automatically activates virtual environment if needed
- **Use case**: Full system validation, CI/CD, before releases

#### `./quick_test.sh`
**Essential tests for rapid feedback**
- Runs only the most critical tests (4 core tests)
- Fast execution for development workflow
- Minimal output for quick feedback
- **Use case**: During development, before commits

#### `./run_test.sh [pattern]`
**Selective test runner**
- Run specific tests by pattern matching
- Examples:
  - `./run_test.sh baseline` - Run baseline test
  - `./run_test.sh bugfix` - Run bugfix-related tests
  - `./run_test.sh U10` - Run U10 tournament test
  - `./run_test.sh pts` - Run Pts./TB column tests
- **Use case**: Targeted testing, debugging specific functionality

## Test Categories

### Core Tournament Import Tests
- **`test_tournament_import_baseline.py`** - Baseline functionality validation
- **`test_U10_tournament.py`** - U10 age category tournament import
- **`test_Vbg_Landesmeisterschaft_2025_U8.py`** - U8 tournament import
- **`test_Vbg_Landesmeisterschaft_2025_U12.py`** - U12 tournament import

### Special Format Tests
- **`test_Best_of_3_MU16.py`** - Best of 3 match format
- **`test_team_tournament.py`** - Team tournament format
- **`test_Bodenseeopen_2025.py`** - Bodenseeopen tournament
- **`test_Rallye_Lustenau_2025_U8.py`** - Rallye Lustenau tournament

### System Feature Tests
- **`test_live_importer_19h.py`** - Live tournament import functionality
- **`test_unrated_detection.py`** - Unrated player detection

### Bugfix and Regression Tests
- **`test_pts_tb_column_detection.py`** - Pts./TB column detection bugfix (comprehensive)
- **`test_bugfix_verification.py`** - Quick bugfix verification
- **`test_regression_pts_tb_columns.py`** - Unit tests for Pts./TB regression

## Test Environment Setup

### Prerequisites
```bash
# Ensure virtual environment is activated
source /home/martin/chesscrew/venv/bin/activate

# Set required environment variable
export FLASK_SECRET_KEY="your-secret-key"
```

### Automatic Setup
All test runners automatically:
- Activate the virtual environment if not already active
- Set the required FLASK_SECRET_KEY
- Clean up temporary files after execution

## Usage Examples

### Run All Tests
```bash
cd /home/martin/chesscrew/backend
./run_all_tests.sh
```

### Quick Development Testing
```bash
cd /home/martin/chesscrew/backend
./quick_test.sh
```

### Test Specific Functionality
```bash
cd /home/martin/chesscrew/backend

# Test baseline functionality
./run_test.sh baseline

# Test U10 tournaments
./run_test.sh U10

# Test bugfix functionality
./run_test.sh bugfix

# Test team tournaments
./run_test.sh team
```

### Run Individual Tests
```bash
cd /home/martin/chesscrew/backend/tests
FLASK_SECRET_KEY="test-key" python test_tournament_import_baseline.py
```

## Test Output

### Success Output
- ✅ Green checkmarks for passed tests
- 🎉 Success celebration for all tests passing
- Summary with total/passed/failed counts

### Failure Output
- ❌ Red X marks for failed tests
- Detailed error output for debugging
- Exit code 1 for failed test suites

## Recent Bugfixes Tested

### Pts./TB Column Detection Bug
**Issue**: Tournaments with both 'Pts.' and TB1/TB2/TB3 columns were incorrectly importing tiebreak values as tournament points.

**Example**: Christina Domig was imported with 23 points (from TB1) instead of 4 points (from Pts. column).

**Tests covering this fix**:
- `test_pts_tb_column_detection.py` - Comprehensive test with both formats
- `test_bugfix_verification.py` - Quick verification test
- `test_regression_pts_tb_columns.py` - Unit tests for regression coverage

**Verification**: Run `./run_test.sh bugfix` to verify the fix is working.

## Adding New Tests

### Test File Naming Convention
- Prefix with `test_`
- Use descriptive names
- End with `.py`

### Test File Structure
```python
#!/usr/bin/env python3
"""
Description of what this test covers
"""

import sys
import os
sys.path.append('/home/martin/chesscrew/backend')

from app import create_app
from db.models import db, Tournament, TournamentPlayer, Game

def test_function():
    """Test implementation"""
    app = create_app()
    with app.app_context():
        # Test implementation here
        pass

if __name__ == "__main__":
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    success = test_function()
    sys.exit(0 if success else 1)
```

### Integration
New tests are automatically discovered by the test runners based on the `test_*.py` naming pattern.

## Troubleshooting

### Common Issues

1. **Virtual Environment Not Active**
   - Test runners will attempt to activate automatically
   - Manually activate: `source /home/martin/chesscrew/venv/bin/activate`

2. **FLASK_SECRET_KEY Not Set**
   - Test runners set this automatically
   - Manually set: `export FLASK_SECRET_KEY="test-key"`

3. **Database Issues**
   - Tests automatically clear the database before running
   - Check database permissions and file access

4. **Import Errors**
   - Ensure you're running from the correct directory
   - Check that all dependencies are installed in the virtual environment

### Debug Individual Tests
```bash
cd /home/martin/chesscrew/backend/tests
FLASK_SECRET_KEY="test-key" python test_name.py
```

This will show full output for debugging specific test failures.
