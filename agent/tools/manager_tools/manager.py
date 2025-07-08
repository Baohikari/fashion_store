from shared.db.queries import add_product
from shared.pinecone.index_product_vectors import index_product_in_pinecone

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
    
manager_tools = [add_product_with_vector]