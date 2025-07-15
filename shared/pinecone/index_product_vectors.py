import uuid
from shared.pinecone.client import get_pinecone_index
from shared.pinecone.embed_utils import get_product_embedding

def index_product_in_pinecone(product_data: dict) -> str:
    index = get_pinecone_index()

    embedding = get_product_embedding(
        product_data["name"],
        product_data["description"],
        product_data["style_tags"],
        product_data["category"],
        product_data["season"]
    )

    vector_id = str(uuid.uuid4())

    metadata = {
        "name": product_data["name"],
        "category": product_data["category"],
        "style_tags": product_data["style_tags"],
        "season": product_data["season"],
        "gender": product_data["gender"],
        "description": product_data["description"],
        "price": product_data["price"]
    }

    index.upsert([(vector_id, embedding, metadata)])
    return vector_id
