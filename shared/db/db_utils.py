from collections import defaultdict
from datetime import datetime, timedelta
import uuid

def group_variants(products: list) -> list:
    """
    Group product variants by base attributes (name, category, etc.)
    and collect sizes and colors into lists.

    Args:
        products (list): List of products from DB (each is a dict)

    Returns:
        list: Grouped product list with combined sizes/colors.
    """
    grouped = {}

    for p in products:
        # Key là những field không thay đổi giữa các biến thể
        key = (
            p["name"],
            p["category"],
            p["description"],
            p["style_tags"],
            p["season"],
            p["gender"],
            p["price"],
            p["image_url"],
        )

        if key not in grouped:
            grouped[key] = {
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "description": p["description"],
                "style_tags": p["style_tags"],
                "season": p["season"],
                "gender": p["gender"],
                "price": p["price"],
                "image_url": p["image_url"],
                "colors": set(),
                "sizes": set()
            }

        grouped[key]["colors"].add(p["color"])
        grouped[key]["sizes"].add(p.get("size", "Unknown"))

    # Convert set -> list để hiển thị
    return [
        {
            **info,
            "colors": list(info["colors"]),
            "sizes": list(info["sizes"])
        }
        for info in grouped.values()
    ]

def get_current_week_range():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.date(), end_of_week.date() 

def generate_order_code():
    now = datetime.now().strftime("%Y%m%d")
    unique = str(uuid.uuid4())[:6].upper()
    return f"ORD{now}{unique}"
