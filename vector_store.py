import os
import numpy as np
import openai
import faiss

openai.api_key = os.getenv("OPENAI_API_KEY")

INDEX_FILE = "faiss.index"
TEXT_FILE = "texts.txt"

def embed_text(texts):
    response = openai.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )
    return [np.array(data.embedding, dtype=np.float32) for data in response.data]

def build_faiss_index(embeddings):
    dim = len(embeddings[0])
    idx = faiss.IndexFlatL2(dim)
    idx.add(np.array(embeddings))
    return idx

def save_faiss_index(idx, filepath=INDEX_FILE):
    faiss.write_index(idx, filepath)

def load_faiss_index(filepath=INDEX_FILE):
    if os.path.exists(filepath):
        return faiss.read_index(filepath)
    return None

def save_texts(text_list, filepath=TEXT_FILE):
    with open(filepath, "w", encoding="utf-8") as f:
        for t in text_list:
            f.write(t.replace("\n", " ") + "\n=====")

def load_texts(filepath=TEXT_FILE):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return content.split("\n=====")

def search_index(query, index, texts, top_k=3):
    query_embedding = embed_text([query])[0]
    D, I = index.search(np.array([query_embedding]), top_k)
    results = [texts[i] for i in I[0] if i < len(texts)]
    return results
