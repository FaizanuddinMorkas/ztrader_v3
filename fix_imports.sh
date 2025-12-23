#!/bin/bash
# Fix import paths for all moved Python scripts

echo "Fixing import paths in moved scripts..."

# Scripts that need fixing (in scripts/utils/, scripts/sync/, scripts/signals/, scripts/database/)
SCRIPTS=(
  "scripts/signals/daily_signals.py"
  "scripts/utils/fetch_fundamentals.py"
  "scripts/utils/extend_instruments.py"
  "scripts/utils/compare_strategies.py"
  "scripts/utils/add_new_stocks.py"
  "scripts/sync/sync_fundamentals.py"
  "scripts/sync/sync_special_stocks.py"
  "scripts/database/seed_nifty100.py"
)

for script in "${SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    echo "Processing: $script"
    
    # Check if it already has the path fix
    if ! grep -q "sys.path.insert(0, str(Path(__file__).parent.parent.parent))" "$script"; then
      # Add the import fix after the imports section
      python3 << EOF
import re

with open('$script', 'r') as f:
    content = f.read()

# Find the position after "from pathlib import Path" or add it
if 'from pathlib import Path' in content:
    # Already has Path import, just add sys.path
    if 'import sys' in content and 'sys.path.insert' not in content:
        # Add after imports
        content = re.sub(
            r'(from pathlib import Path\n)',
            r'\1\n# Add project root to path\nsys.path.insert(0, str(Path(__file__).parent.parent.parent))\n',
            content
        )
else:
    # Need to add both Path import and sys.path
    content = re.sub(
        r'(import sys\n)',
        r'\1from pathlib import Path\n\n# Add project root to path\nsys.path.insert(0, str(Path(__file__).parent.parent.parent))\n',
        content
    )

with open('$script', 'w') as f:
    f.write(content)
EOF
    fi
  fi
done

echo "Done!"
