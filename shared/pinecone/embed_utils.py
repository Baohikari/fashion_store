from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_product_embedding(name: str, description: str, style_tags: str, category: str, color: str, season: str):
    text = f"{name}. {description}. Category: {category}. Tags: {style_tags}. Color: {color}. Season: {season}."
    return model.encode(text).tolist()
