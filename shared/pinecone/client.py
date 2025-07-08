import os
from dotenv import load_dotenv
from pinecone import Pinecone, PodSpec

load_dotenv()

# Tạo client Pinecone mới
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Lấy index (giả sử đã tạo sẵn trên dashboard)
def get_pinecone_index(index_name="fashion-style"):
    return pc.Index(index_name)
