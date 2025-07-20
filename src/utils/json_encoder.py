"""
Custom JSON encoder for handling special data types in API responses.
"""
import json
from datetime import datetime, date
import pandas as pd
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles special data types:
    - datetime objects
    - date objects
    - pandas Timestamp objects
    - numpy numeric types
    """
    
    def default(self, obj: Any) -> Any:
        """
        Convert special data types to JSON serializable types.
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON serializable representation of the object
        """
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat().replace('+00:00', 'Z')
        
        # Handle date objects
        if isinstance(obj, date):
            return obj.isoformat()
        
        # Handle pandas Timestamp objects
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat().replace('+00:00', 'Z')
        
        # Handle numpy numeric types
        try:
            import numpy as np
            if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8,
                              np.int16, np.int32, np.int64, np.uint8,
                              np.uint16, np.uint32, np.uint64)):
                return int(obj)
            elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.bool_)):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
        except ImportError:
            pass
        
        # Let the base class handle it or raise TypeError
        return super().default(obj)