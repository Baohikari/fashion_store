from shared.db.queries import search_products_by_keyword
from google.adk.tools import ToolContext

def get_product_by_keyword(keyword: str, tool_context: ToolContext = None) -> dict:
    """
    Get all products matching a keyword based on name, description, style_tags, category.

    Args: 
        keyword (str): keyword to compare with name, description, style_tags, category.
        tool_context (ToolContext): used to save for later operations.

    Returns:
        dict: {
            status: success or failed.
            message: str
        }
    """
    try:
        products = search_products_by_keyword(keyword)
        if not products:
            return {
                "status": "failed",
                "message": f"No products found for keyword '{keyword}'."
            }
        
        message = f"Found {len(products)} product(s):\n"
        for p in products:
            message += f"= {p['name']} ({p['category']}, {p['color']}): {p['price']}$"
            message += f"{p['image_url']}\n"

        return {
            "status": "success",
            "message": message
        }
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Error occured: {str(e)}."
        }
    
customer_tools = [get_product_by_keyword]