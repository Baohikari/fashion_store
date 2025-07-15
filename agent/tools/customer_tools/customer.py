from shared.db.queries import search_products_by_keyword, add_order
from google.adk.tools import ToolContext, FunctionTool
from ..utils import paginate
from shared.db.db_utils import group_variants
from shared.pinecone.client import get_pinecone_index
from shared.pinecone.embed_utils import get_product_embedding
from google.adk.tools import FunctionTool
import uuid
from shared.pinecone.embed_utils import get_product_embedding

def get_product_by_keyword(keyword: str, page: int = 1, page_size: int = 5, tool_context: ToolContext = None) -> dict:
    """
    Search for products using a keyword and return paginated results.

    This tool searches product data based on `keyword` matched in name, description, tags or category, gender.
    If results are found, they will be grouped and stored into `tool_context["last_search_results"]`
    for use in other tools like detail view or cart.

    Args:
        keyword (str): Keyword or phrase to search (e.g., "tank top", "summer jacket").
        page (int): Page number of the results to return.
        page_size (int): Number of items per page.
    Returns:
        dict: {
            "status": "success" or "failed",
            "message": Search result summary
        }
    """
    try:
        raw_products = search_products_by_keyword(keyword)

        if not raw_products:
            return {
                "status": "failed",
                "message": f"No products found for keyword '{keyword}'."
            }

        # Defensive check: ensure all required keys exist
        for p in raw_products:
            for key in ["description", "style_tags", "season", "gender"]:
                if key not in p:
                    p[key] = "N/A"  # prevent KeyError in group_variants

        grouped_products = group_variants(raw_products)

        if tool_context is not None:
            tool_context.state["last_search_results"] = grouped_products


        pagination = paginate(grouped_products, page=page, page_size=page_size)
        paged_products = pagination['data']

        message = f"🔍 Found {pagination['total_items']} product(s) for '{keyword}'. Showing page {pagination['page']} of {pagination['total_pages']}:\n\n"
        for idx, p in enumerate(paged_products, start=1):
            message += (
                f"{idx}. {p['name']} ({p['category']}): {p['price']}$\n"
                f"   Colors: {', '.join(p.get('colors', []))}\n"
                f"   {p['image_url']}\n\n"
            )

        return {
            "status": "success",
            "message": message
        }

    except Exception as e:
        return {
            "status": "failed",
            "message": f"❌ Error occurred while searching: {str(e)}"
        }

    
def get_product_details(index: int, tool_context: ToolContext) -> dict:
    """
    Show detailed information of a product from either:
    - the last search result (search by keyword), or
    - the last outfit advised.

    Priority:
    - If 'last_search_results' exists -> use it
    - Else if 'last_outfit_suggestion' exists -> convert outfit dict to list by order: topwear, bottomwear, footwear, accessories

    Args:
        index (int): 1-based index of the product to view.
        tool_context (ToolContext): Provided by ADK framework.

    Returns:
        dict: {
            status: "success" or "failed",
            message: str
        }
    """
    try:
        # Try search results first
        results = tool_context.state.get("last_search_results")

        if results:
            source = "search"
        else:
            # Fallback to outfit suggestion
            outfit = tool_context.state.get("last_outfit_suggestion")
            if outfit:
                results = [v for v in outfit.values() if v is not None]
                source = "outfit"
            else:
                return {
                    "status": "failed",
                    "message": "Please search for products or request an outfit first."
                }

        if index < 1 or index > len(results):
            return {
                "status": "failed",
                "message": f"Invalid index. Please choose between 1 and {len(results)} based on the displayed list."
            }

        product = results[index - 1]
        message = (
            f"🎯 --------- {product['name']} ---------\n\n"
            f"1. 💰 Price: {product['price']}$\n"
            f"2. 📦 Quantity: {product.get('quantity', 'N/A')}\n"
            f"3. 🏷️ Category: {product['category']}\n"
            f"4. 🔢 ID: {product.get('id', 'N/A')}\n"
            f"5. 📝 Description:\n{product['description']}\n"
            f"6. 🧵 Style Tags: {product['style_tags']}\n"
            f"7. ❄️ Season: {product['season']}    "
            f"8. 🚻 Gender: {product['gender']}\n"
            f"9. 🎨 Colors: {', '.join(product.get('colors', [])) if isinstance(product.get('colors'), list) else product.get('color', 'N/A')}\n"
            f"10. Image link: {product['image_url']}"
        )

        return {
            "status": "success",
            "message": message
        }

    except Exception as e:
        return {
            "status": "failed",
            "message": f"Error occurred while getting product details: {str(e)}"
        }


def add_to_cart(index: int, quantity: int = 1, tool_context: ToolContext = None) -> dict:
    """
    Add a product to the shopping cart based on its index in the last search results or outfit suggestion.

    This function retrieves the last product search or outfit suggestion from the tool context,
    finds the product at the given index (1-based), and adds it to the cart. If the product already
    exists in the cart, it increments the quantity.

    Args:
        index (int): 1-based index of the product in the last search result or outfit suggestion.
        quantity (int, optional): Number of units to add. Defaults to 1.
        tool_context (ToolContext, optional): Agent context containing previous search results and the cart.

    Returns:
        dict: A dictionary with keys:
            - "status": "success" or "failed"
            - "message": Description of the result
    """
    if tool_context is None:
        return {
            "status": "failed",
            "message": "No session context found."
        }
    results = tool_context.state.get("last_search_results") or [
        v for v in tool_context.state.get("last_outfit_suggestion", {}).values() if isinstance(v, dict)
    ]
    if not results or index < 1 or index > len(results):
        return {
            "status": "failed",
            "message": "Invalid product index."
        }
    product = results[index - 1]
    cart = tool_context.state.get("cart", [])

    for item in cart:
        if item["product_id"] == product["id"]:
            item["quantity"] += quantity
            break
    else:
        cart.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": quantity,
            "unit_price": product["price"]
        })
    tool_context["cart"] = cart
    return {
        "status": "success",
        "message": f"Added {quantity} of '{product['name']}' to your cart."
    }

def view_cart(tool_context: ToolContext = None) -> dict:
    """
    View the contents of the current shopping cart stored in the tool context.

    Iterates through the cart and formats a detailed summary of items and the total amount.

    Args:
        tool_context (ToolContext, optional): Agent context that holds the current shopping cart.

    Returns:
        dict: A dictionary with keys:
            - "status": "success"
            - "message": A detailed list of cart contents or notice if empty.
    """
    cart = tool_context.state.get("cart", [])
    if not cart:
        return {
            "status": "success",
            "message": "Your cart is currently empty."
        }
    message = "Your cart:\n\n"
    total = 0
    for i, item in enumerate(cart, 1):
        line_total = item["unit_price"] * item["quantity"]
        total += line_total
        message += f"{i}. {item["product_name"]} x {item["quantity"]} = {line_total}$\n"
    message += f"\nTotal: {total}$"
    return {
        "status": "success",
        "message": message
    }

def place_order(customer_name: str, phone: str, comment: str = "", tool_context: ToolContext = None) -> dict:
    """
    Finalize and place an order based on the current contents of the cart.

    For each product in the cart, this function stores the order using `add_order`,
    then clears the cart from the session context.

    Args:
        customer_name (str): Name of the customer placing the order.
        phone (str): Customer's phone number for contact or delivery.
        comment (str, optional): Additional comment or note from the customer.
        tool_context (ToolContext, optional): Agent context containing the shopping cart.

    Returns:
        dict: A dictionary with keys:
            - "status": "success" or "failed"
            - "message": Order confirmation or error message
    """
    cart = tool_context.state.get("cart", [])
    if not cart:
        return {
            "status": "failed",
            "message": "Your cart is empty."
        }
    for item in cart:
        total_price = item["unit_price"] * item["quantity"]

        order_data = {
            "customer_name": customer_name,
            "phone": phone,
            "product_name": item["product_name"],
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total_price": total_price,
        }
        add_order(order_data)
    tool_context["cart"] = []
    return {
        "status": "success",
        "message": "Order placed successfully. Thank u for shopping."
    }
THRESHOLD = 0.8

CATEGORY_MAP = {
    "topwear": ["top", "shirt", "blouse", "tank", "tee"],
    "bottomwear": ["bottom", "pants", "jeans", "skirts", "shorts"],
    "footwear": ["shoe", "footwear", "sneaker", "boots", "heels", "sandals"],
    "accessories": ["accessories", "belt", "watch", "bracelet", "hat", "bag", "sunglass", "necklace"]
}

def is_contextually_suitable(item, prompt: str) -> bool:
    category = item.get("category", "").lower()
    prompt = prompt.lower()
    if "swim" in category and not any(w in prompt for w in ["beach", "pool", "swimming", "sea", "vacation"]):
        return False
    if "sleep" in category and not any(w in prompt for w in ["sleep", "pajamas", "night", "bed"]):
        return False
    if "sport" in category or "gym" in category:
        if not any(w in prompt for w in ["sport", "exercise", "run", "gym", "training", "fitness"]):
            return False
    if "outerwear" in category or "coat" in category or "jacket" in category:
        if not any(w in prompt for w in ["cold", "winter", "windy", "rain", "chilly"]):
            return False
    return True

def match_category(item, keywords):
    cat = item.get("category", "").lower()
    return any(kw in cat for kw in keywords)

def advise_outfit(prompt: str, tool_context: ToolContext = None) -> dict:
    """
    Generate a complete outfit suggestion based on the user's style prompt and context.

    This tool uses vector similarity search to find clothing items (e.g. tops, bottoms, footwear, accessories)
    that best match the user's style or occasion described in the `prompt`. It also considers session context
    like season, gender, or style_tags if available, to provide more relevant recommendations.

    The final outfit includes:
    - One topwear (e.g., shirt, blouse)
    - One bottomwear (e.g., pants, skirt)
    - One footwear (e.g., sneakers, sandals)
    - Up to 3 accessories (optional)

    Excluded items (e.g. swimwear in winter) are listed separately as "others".

    The result is also stored in session state (`tool_context.state["last_outfit_suggestion"]`) for later use
    in tools like `get_product_details`, `change_outfit_part`, or `add_to_cart`.

    Args:
        prompt (str): A short natural language description of the desired outfit or occasion.
            Examples:
                - "an elegant outfit for a rooftop party"
                - "a casual look for summer picnic"
                - "something warm for rainy weather"

    Returns:
        dict: {
            "status": "success" | "failed" | "error",
            "message": "Detailed outfit description with product names, prices and image URLs"
        }

    When to use:
        - Use this tool when the user wants a fashion suggestion, outfit idea, or asks for recommendations
        based on a specific style, event, or weather.
        - Always run this tool before using product detail or cart-related tools based on an outfit.

    Examples:
        >>> advise_outfit("a classy outfit for a formal dinner")
        {
            "status": "success",
            "message": "Recommended outfit: White silk blouse ($89), Black tailored trousers ($120), Nude heels ($150), Gold clutch ($60), Pearl earrings ($45)."
        }

        >>> advise_outfit("something cozy for winter trip")
        {
            "status": "success",
            "message": "Recommended outfit: Wool turtleneck sweater ($70), Thermal leggings ($55), Winter boots ($130), Knitted scarf ($25), Beanie hat ($20)."
        }

        >>> advise_outfit("beachwear for summer vacation")
        {
            "status": "success",
            "message": "Recommended outfit: Floral crop top ($40), Denim shorts ($45), Flip-flops ($20), Sunglasses ($30), Straw hat ($25)."
        }
    """

    try:
        index = get_pinecone_index()
        # Get session state
        season = tool_context.state.get("season", "")
        gender = tool_context.state.get("gender", "")
        style_tags = tool_context.state.get("style_tags", "")

        # Get embedding
        embedding = get_product_embedding(prompt, season, gender, style_tags, "")
        matches = index.query(vector=embedding, top_k=50, include_metadata=True)
        filtered = [m for m in matches["matches"] if m["score"] >= THRESHOLD]

        if not filtered:
            return {
                "status": "failed",
                "message": "Sorry, I couldn't find any suitable items for that style."
            }

        items = [m["metadata"] for m in filtered]
        grouped = group_variants(items)

        # Create empty outfit
        outfit = {
            "topwear": None,
            "bottomwear": None,
            "footwear": None,
            "accessories": [],
            "others": []
        }

        for item in grouped:
            if not is_contextually_suitable(item, prompt):
                outfit["others"].append(item)
                continue

            cat = item.get("category", "").lower()
            if not outfit["topwear"] and match_category(item, CATEGORY_MAP["topwear"]):
                outfit["topwear"] = item
            elif not outfit["bottomwear"] and match_category(item, CATEGORY_MAP["bottomwear"]):
                outfit["bottomwear"] = item
            elif not outfit["footwear"] and match_category(item, CATEGORY_MAP["footwear"]):
                outfit["footwear"] = item
            elif match_category(item, CATEGORY_MAP["accessories"]):
                outfit["accessories"].append(item)
            else:
                outfit["others"].append(item)

        # Write advising resuls in session state
        tool_context.state["last_outfit_suggestion"] = outfit

        # write style (if can guess from prompt)
        if "casual" in prompt.lower():
            tool_context.state["style_tags"] = "casual"
        elif "formal" in prompt.lower():
            tool_context.state["style_tags"] = "formal"

        def fmt(label, item):
            if not item:
                return f"{label}: ❌ Not found\n"
            return f"{label}: {item['name']} - {item['price']}$\n{item['image_url']}\n"

        message = f"👗 Outfit suggestion for: **{prompt}**\n\n"
        message += fmt("👕 Topwear", outfit["topwear"])
        message += fmt("👖 Bottomwear", outfit["bottomwear"])
        message += fmt("👟 Footwear", outfit["footwear"])

        if outfit["accessories"]:
            message += "\n👜 Accessories:\n"
            for acc in outfit["accessories"][:3]:
                message += f" - {acc['name']} ({acc['price']}$)\n{acc['image_url']}\n"
        else:
            message += "\n👜 Accessories: Not found.\n"

        if outfit["others"]:
            message += f"\n⚠️ {len(outfit['others'])} item(s) were excluded due to style mismatch."

        return {
            "status": "success",
            "message": message
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Something went wrong while generating outfit: {str(e)}"
        }

def change_outfit_part(part: str, prompt: str, tool_context: ToolContext = None) -> dict:
    """
    """
    try:
        outfit = tool_context.state.get("last_outfit_suggestion")
        if not outfit:
            return {
                "status": "error",
                "message": "There is no previous advising outfit."
            }
        season = tool_context.state.get("season", "")
        gender = tool_context.state.get("gender", "")
        style_tags = tool_context.state.get("style_tags", "")

        index = get_pinecone_index()
        embedding = get_product_embedding(prompt, season, gender, style_tags, "")
        matches = index.query(vector=embedding, top_k=30, include_metadat=True)

        filtered = [m["metadata"] for m in matches["matches"] if m["score"] >= THRESHOLD]
        grouped = group_variants(filtered)

        found = None
        if part not in CATEGORY_MAP:
            return {
                "status": "error",
                "message": f"Unsupported outfit part: {part}"
            }
        for item in grouped:
            if match_category(item, CATEGORY_MAP[part]):
                found = item
                break
        if not found:
            return {
                "status": "error",
                "message": f"Sorry, couldn't found a suitable alternative for {part}."
            }
        if part == "accessories":
            outfit["accessories"] = [found]
        else:
            outfit[part] = found
        
        tool_context.state["last_outfit_suggestion"] = outfit

        return {
            "status": "success",
            "message": f"✅ New {part} suggestion: {found['name']} - {found['price']}$\n{found['image_url']}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Something went wrong while replacing {part}: {str(e)}."
        }
    

get_product_by_keyword = FunctionTool(func=get_product_by_keyword)
get_product_details = FunctionTool(func=get_product_details)
add_to_cart = FunctionTool(func=add_to_cart)
view_cart = FunctionTool(func=view_cart)
place_order = FunctionTool(func=place_order)
advise_outfit = FunctionTool(func=advise_outfit)
change_outfit_part = FunctionTool(func=change_outfit_part)

customer_tools = [get_product_by_keyword, get_product_details, add_to_cart, view_cart, place_order, advise_outfit]