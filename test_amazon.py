from src.integrations.amazon.amazon_api import _search_items
import os

try:
    items = _search_items(
        search_index="VideoGames",
        browse_node_id=None,
        keywords=None,
        min_saving_percent=1,
        sort_by=None,
        item_count=100,
    )
    print(f"Got {len(items)} items with item_count=100")
except Exception as e:
    print(f"Error: {e}")
