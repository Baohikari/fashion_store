from shared.db.connection import get_connection
from datetime import datetime
from .db_utils import get_current_week_range, generate_order_code

# ======================== PRODUCTS ===========================================================

def convert_drive_link_to_direct(link: str) -> str:
    import re
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return link 

def search_products_by_keyword(keyword: str, limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    keywords = keyword.lower().split()
    like_clauses = []
    params = []

    for word in keywords:
        wildcard = f"%{word}%"
        for field in ["name", "description", "style_tags", "category", "gender"]:
            like_clauses.append(f"{field} LIKE %s")
            params.append(wildcard)

    where_clause = " OR ".join(like_clauses)
    query = f"""
        SELECT id, name, category, price, color, image_url,
               description, style_tags, season, gender
        FROM products
        WHERE {where_clause}
        LIMIT %s;
    """
    params.append(limit)

    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        print("❌ Error in search_products_by_keyword:", e)
        return []
    finally:
        cursor.close()
        conn.close()


def get_all_product():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT * FROM products
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        print("Get products successfully.")
        return results
    except Exception as e:
        print(f"Failed to get all products {str(e)}.")
        return []
    finally:
        cursor.close()
        conn.close()

def get_product_by_id(product_id: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
    SELECT * FROM products WHERE id=%s
    """
    try:
        cursor.execute(query, (product_id,))
        results = cursor.fetchall()
        print("Get product by id successfully.")
        return results
    except Exception as e:
        print(f"Failed to get product by id {str(e)}.")
        return []
    finally:
        cursor.close()
        conn.close()
    

def add_product(product_data: dict):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    image_url = convert_drive_link_to_direct(product_data["img_url"])
    query = """
        INSERT INTO products (
            name, category, price, description, style_tags,
            color, season, gender, image_url, vector_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    values = (
        product_data["name"],
        product_data["category"],
        product_data["price"],
        product_data["description"],
        product_data["style_tags"],
        product_data["color"],
        product_data["season"],
        product_data["gender"],
        image_url,
        product_data["vector_id"],
    )

    try:
        cursor.execute(query, values)
        conn.commit()
        print("Product added successfully.")
    except Exception as e:
        print("Failed to add product: ", e)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def update_product(product_id: str, updated_data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    set_clause = ", ".join(f"{key} = %s" for key in updated_data.keys())
    values = list(updated_data.values())

    query= f"""
    UPDATE products SET {set_clause} WHERE id = %s
    """
    try:
        cursor.execute(query, values + [product_id])
        conn.commit()
        print("Product updated successfully.")
    except Exception as e:
        conn.rollback()
        print("Error updating product:", e)
    finally:
        cursor.close()
        conn.close()

def remove_product(product_id: str) -> bool:
    """
    Permanently remove a product from the database using its unique ID.

    Args:
        product_id (str): The ID of the product to be deleted.

    Returns:
        bool: True if a product was deleted, False if not found or error occurred.
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = "DELETE FROM products WHERE id = %s"
    
    try:
        cursor.execute(query, (product_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✅ Product {product_id} removed.")
            return True
        else:
            print(f"⚠️ Product {product_id} not found.")
            return False
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to remove product {product_id}: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()



# =================ORDERS===================================================

def add_order(order_data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    created_time = datetime.now().isoformat()
    order_code = generate_order_code()
    query = """INSERT INTO orders (
    customer_name, phone, product_name, product_id, quantity, unit_price, total_price, order_code
    )
    VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        order_data["customer_name"],
        order_data["phone"],
        order_data["product_name"],
        order_data["product_id"],
        order_data["quantity"],
        order_data["unit_price"],
        order_data["total_price"],
        order_code,
    )
    try:
        cursor.execute(query, values)
        conn.commit()
        print("Order added successfully.")
    except Exception as e:
        print("Failed to add order: ", e)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_weekly_orders_query():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    start, end = get_current_week_range()
    query = f"""
    SELECT * FROM orders WHERE order_date BETWEEN '{start}' AND '{end}'
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        print("Get all the orders in the week successfully.")
        return results
    except Exception as e:
        print(f"Failed to get orders {str(e)}.")
        return []
    finally:
        cursor.close()
        conn.close()


# ===============================FEEDBACKS========================================

def get_weekly_feedbacks_query():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    start, end  = get_current_week_range()
    query=f"""
    SELECT * FROM feedbacks WHERE created_date BETWEEN {start} AND {end}
    """
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        print("Get all the weekly feedbacks successfully.")
        return results
    except Exception as e:
        print(f"Failed to get all the weekly feedbacks.")
        return []
    finally:
        cursor.close()
        conn.close()