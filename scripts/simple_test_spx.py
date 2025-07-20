"""
Simple test script to verify that the handler works with ^SPX ticker.
"""
import sys
sys.path.append('.')

from handler import get_options_analytics

def test_handler_with_spx():
    """Test the handler with ^SPX ticker."""
    print("Testing handler with ^SPX ticker...")
    
    # Create a mock event with ^SPX ticker
    event = {
        'httpMethod': 'GET',
        'path': '/options-analytics',
        'queryStringParameters': {
            'ticker': '^SPX'
        },
        'headers': {},
        'requestContext': {
            'requestId': 'test-request-id'
        }
    }
    
    # Call the handler
    try:
        response = get_options_analytics(event, {})
        
        # Check response status code
        status_code = response.get('statusCode')
        print(f"Response status code: {status_code}")
        
        if status_code == 200:
            print("✓ Handler successfully processed ^SPX ticker")
            
            # Extract some data from the response
            import json
            body = json.loads(response.get('body', '{}'))
            
            ticker = body.get('ticker')
            stock_price = body.get('stock', {}).get('price')
            expiration_count = len(body.get('expirationDates', []))
            
            print(f"  Ticker: {ticker}")
            print(f"  Stock price: {stock_price}")
            print(f"  Expiration dates: {expiration_count}")
            
            if expiration_count > 0:
                first_exp = body.get('expirationDates', [])[0]
                exp_date = first_exp.get('expiration')
                calls_count = len(first_exp.get('calls', []))
                puts_count = len(first_exp.get('puts', []))
                
                print(f"  First expiration: {exp_date}")
                print(f"  Calls: {calls_count}, Puts: {puts_count}")
        else:
            print(f"✗ Handler failed with status code {status_code}")
            print(f"  Error: {response.get('body')}")
    
    except Exception as e:
        print(f"✗ Handler threw an exception: {e}")

if __name__ == "__main__":
    print("Testing handler with ^SPX ticker...\n")
    
    # Run test
    test_handler_with_spx()
    
    print("\nTest completed.")