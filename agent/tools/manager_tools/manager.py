from shared.db.queries import add_product, remove_product, get_all_product, update_product, get_weekly_orders_query, get_weekly_feedbacks_query
from shared.pinecone.index_product_vectors import index_product_in_pinecone
import pandas as pd
import os
from google.adk.tools import FunctionTool
import datetime
from google.adk.tools import ToolContext

def get_all_product_and_export() -> dict:
    """
    Read all products that are currently in table "products"
    and exports them into an Excel file, the file has format name: "<YYYY-MM-DD_HH-MM-SS>_product.xlsx".

    Returns:
        dict: {
            "status": "success" or "error".
            "message": str.
        }
    """
    try:
        products = get_all_product()
        if not products:
            return {
                "status": "error",
                "message": "No product found in table 'products'."
            }
        
        df = pd.DataFrame(products)

        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_products.xlsx"
        filepath = os.path.join(export_dir, filename)

        df.to_excel(filepath, index=False)
        return {
            "status": "success",
            "message": f"Exported {len(df)} products to file: {filepath}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to export products: {str(e)}"
        }


def add_product_with_vector(product_data: dict) -> str:
    """
    Collects and processes product information provided by the manager, generates a vector embedding 
    for style matching using Pinecone, and stores both metadata and the vector ID into the database.

    Args:
        product_data (dict): A dictionary containing product details including:
            - name (str): The name of the product.
            - category (str): The category the product belongs to (e.g., T-Shirts, Shoes).
            - price (float): The price of the product.
            - description (str): A textual description of the product.
            - style_tags (str): Comma-separated tags describing the style (e.g., casual, sporty).
            - color (str): Primary color of the product.
            - season (str): Suitable season for the product (e.g., summer, winter).
            - gender (str): Target gender (e.g., male, female, unisex).
            - img_url (str): Google Drive or direct link to the product image.

    Returns:
        str: A message indicating whether the product was successfully added and indexed,
            or describing any error that occurred.
    """
    try:
        vector_id = index_product_in_pinecone(product_data)

        product_data['vector_id'] = vector_id

        add_product(product_data)

        return "Product has been added and indexed successfully."
    except Exception as e:
        return f"Failed to add product: {str(e)}"

def update_exisiting_product(product_id: str, updated_data: dict) -> str:
    """
    Update an existing product with new data.

    Args:
        product_id (str): ID of the product to update.
        updated_data (dict): Fields to update.

    Returns:
        Message (str).
    """
    try:
        embedding_fields = {"name", "description", "style_tags", "category", "season"}

        if embedding_fields.intersection(updated_data.keys()):
            all_products = get_all_product()
            existing_product = next((p for p in all_products if p["id"] == product_id), None)

            if not existing_product:
                return f"Product with ID: {product_id} not found."
            full_product = {**existing_product, **updated_data}

            new_vector_id = index_product_in_pinecone(full_product)
            updated_data['vector_id'] = new_vector_id
        update_product(product_id, updated_data)
        return "Product has been updated successfully."
    except Exception as e:
        return f"Failed to update product: {str(e)}"

    
def remove_a_product(product_id: str) -> dict:
    """
    Remove a product from the database by its ID, including metadata and vector.

    This function attempts to delete a product from the products table. It first checks
    if the product exists, and then calls the `remove_product` function. It returns
    a detailed status message depending on whether the deletion was successful.

    Args:
        product_id (str): The ID of the product to be removed.

    Returns:
        dict: {
            "status": "success" | "failed",
            "message": str
        }
    """
    try:
        products = get_all_product()
        matched = next((p for p in products if str(p["id"]) == str(product_id)), None)

        if not matched:
            return {
                "status": "failed",
                "message": f"No product with ID {product_id} found."
            }

        success = remove_product(product_id)

        if success:
            return {
                "status": "success",
                "message": f"✅ Product {product_id} removed successfully."
            }
        else:
            return {
                "status": "failed",
                "message": f"❌ Failed to remove product {product_id}. It may have already been deleted."
            }

    except Exception as e:
        return {
            "status": "failed",
            "message": f"❌ Error occurred while removing product {product_id}: {str(e)}"
        }

    
def generate_weekly_report(tool_context: ToolContext=None) -> dict:
    """
    Export a weekly report
    """
    try:
        revenue = 0
        total_sold_unit = 0
        week_orders = get_weekly_orders_query()
        products = get_all_product()
        week_feedbacks = get_weekly_feedbacks_query()

        if not week_orders or not products or not week_feedbacks:
            return {
                "status": "error",
                "message": "Can not found any of information. Please check!"
            }
        for total_price in week_orders["total_price"]:
            revenue += total_price
        
        for total_unit in week_orders["quantity"]:
            total_sold_unit += total_unit
        
        
    except Exception as e:
        pass


def read_and_process_policy(): pass


get_all_product_and_export = FunctionTool(func=get_all_product_and_export)
add_product_with_vector = FunctionTool(func=add_product_with_vector)
update_exisiting_product = FunctionTool(func=update_exisiting_product)
remove_a_product = FunctionTool(func=remove_a_product)

    
manager_tools = [add_product_with_vector, get_all_product_and_export, update_exisiting_product, remove_a_product]