# Pagination
from datetime import datetime, timedelta

def paginate(items, page=1, page_size=10):
    """
    Paginate a list of items.

    Args:
        items (list): The full list of items.
        page (int): The page number (1-based).
        page_size (int): Number of items per page.

    Returns:
        dict: {
            'page': current page number,
            'page_size': page size,
            'total_items': total number of items,
            'total_pages': total number of pages,
            'data': the paginated items
        }
    """
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size  # ceil
    start = (page - 1) * page_size
    end = start + page_size
    data = items[start:end]

    return {
        'page': page,
        'page_size': page_size,
        'total_items': total_items,
        'total_pages': total_pages,
        'data': data
    }


