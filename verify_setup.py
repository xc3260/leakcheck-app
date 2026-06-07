import sys
from leakcheck import LeakCheckAPI_Public

def main():
    print("Testing LeakCheck Public API wrapper...")
    api = LeakCheckAPI_Public()
    try:
        # Querying the public API endpoint for an email
        result = api.lookup(query="test@example.com")
        print("Success! API response received:")
        print(result)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
