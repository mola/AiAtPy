# persian_embedding.py
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch

class PersianEmbeddingSearch:
    def __init__(self, embedding_model='heydariAI/persian-embeddings', 
                 faiss_index_file="resources/faiss_index_heydariAI_IndexFlatL2_short.idx"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(embedding_model)
        self.model = AutoModel.from_pretrained(embedding_model).to(self.device)
        self.index = faiss.read_index(faiss_index_file)
        
    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        res = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        res = res / torch.norm(res, dim=1)[:, None]
        return res
    
    def get_embedding(self, text):
        with torch.no_grad():
            inputs = self.tokenizer([text], return_tensors="pt", padding=True, truncation=True).to(self.device)
            outputs = self.model(**inputs)
            embedding = self._mean_pooling(outputs, inputs['attention_mask']).detach().cpu().numpy()
        return embedding
    
    def find_similar(self, query_text, k=20):
        query_embedding = self.get_embedding(query_text)
        distances, indices = self.index.search(query_embedding, k)
        return distances[0], indices[0]