from src.utils.web_tools import perform_web_search

def test_search():
    query = "DeepSeek v3 benchmarks"
    print(f"Testing search for: {query}")
    results = perform_web_search(query)
    print(f"Number of results: {len(results)}")
    if results:
        print(f"First title: {results[0]['title'].encode('ascii', 'ignore').decode('ascii')}")

if __name__ == "__main__":
    test_search()
