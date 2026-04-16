import sys
import os
import tempfile
sys.path.insert(0, ".")

from tests.random_generator import create_random_fixture
from app.parser import parse_excel

# Create a test file
filepath = create_random_fixture(10, 3)
print(f"Created: {filepath}")
print(f"Exists: {os.path.exists(filepath)}")

# Try to parse it
comps, errors = parse_excel(str(filepath))
print(f"Competitors: {len(comps)}")
print(f"Errors: {errors}")

# Clean up
try:
    os.unlink(filepath)
except:
    pass