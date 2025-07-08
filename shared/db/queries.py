from shared.db.connection import get_connection


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

    query = """
        SELECT id, name, category, price, color, image_url
        FROM products
        WHERE name LIKE %s OR description LIKE %s OR style_tags LIKE %s OR category LIKE %s
        LIMIT %s;
    """
    wildcard = f"%{keyword}%"
    params = (wildcard, wildcard, wildcard, wildcard, limit)

    cursor.execute(query, params)
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

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
        product_data["vector_id"]
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