"""
Fix for the timestamp serialization issue in the handler.
This script adds a JSON encoder that can handle Timestamp objects.
"""
import sys
sys.path.append('.')

from src.utils.time_utils import format_timestamp_for_api
import json
from datetime import datetime
import pandas as pd

def test_timestamp_serialization():
    """Test timestamp serialization."""
    print("Testing timestamp serialization...")
    
    # Create a timestamp object
    timestamp = pd.Timestamp('2025-07-20 12:00:00')
    
    # Try to serialize it directly
    try:
        json_str = json.dumps({"timestamp": timestamp})
        print("✓ Direct serialization worked (unexpected)")
    except TypeError as e:
        print(f"✗ Direct serialization failed as expected: {e}")
    
    # Create a custom JSON encoder
    class TimestampJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    
    # Try to serialize with the custom encoder
    try:
        json_str = json.dumps({"timestamp": timestamp}, cls=TimestampJSONEncoder)
        print(f"✓ Custom encoder serialization worked: {json_str}")
    except TypeError as e:
        print(f"✗ Custom encoder serialization failed: {e}")
    
    # Test the format_timestamp_for_api function
    try:
        formatted = format_timestamp_for_api(timestamp)
        print(f"✓ format_timestamp_for_api worked: {formatted}")
        
        # Try to serialize the formatted timestamp
        json_str = json.dumps({"timestamp": formatted})
        print(f"✓ Serialization of formatted timestamp worked: {json_str}")
    except Exception as e:
        print(f"✗ format_timestamp_for_api failed: {e}")

def create_fix_patch():
    """Create a patch for the handler.py file."""
    print("\nCreating fix patch...")
    
    # Define the patch
    patch = """
# Add this at the top of handler.py after the imports
class TimestampJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):  # Handle datetime and pandas Timestamp objects
            return obj.isoformat()
        return super().default(obj)

# Then replace the line:
#     response_body = json.dumps(response_data)
# with:
#     response_body = json.dumps(response_data, cls=TimestampJSONEncoder)
"""
    
    print(patch)
    
    print("\nTo apply this fix, modify handler.py to:")
    print("1. Add the TimestampJSONEncoder class after the imports")
    print("2. Use this encoder when calling json.dumps()")

if __name__ == "__main__":
    print("Testing and fixing timestamp serialization issue...\n")
    
    # Run tests
    test_timestamp_serialization()
    
    # Create fix patch
    create_fix_patch()