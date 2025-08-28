# embedding_search.py

import faiss
import numpy as np
import pickle
from transformers import AutoModel
from transformers import AutoTokenizer
import torch
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class EmbeddingSearch:
    def __init__(self):
        self.d = 1024
        self.k = 10
        self.index_method = 'IndexFlatL2'
        self.embedding_model = 'heydariAI/persian-embeddings'
        self.faiss_index_file = "/home/arisa/diar/checkpoints/faiss_index_heydariAI_IndexFlatL2_checkpoint_1037000.idx"
        self.pickle_map_file = "/home/arisa/diar/checkpoints/faiss_to_section_map.pkl"

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # self.device = torch.device("cpu")
        print(f"Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(self.embedding_model)
        self.model = AutoModel.from_pretrained(self.embedding_model).to(self.device)

        self.index = faiss.read_index(self.faiss_index_file)
        print(f"Loaded FAISS index from {self.faiss_index_file}")

        with open(self.pickle_map_file, 'rb') as f:
            self.faiss_to_section_map = pickle.load(f)
            print(f"Loaded faiss_to_section_map from {self.pickle_map_file}")

    def mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        res = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        res = res / torch.norm(res, dim=1)[:, None]
        return res

    def get_section_ids(self, new_section):
        mapped_sections = []
        try:
            print("start retreive")
            with torch.no_grad():
                print("prompt: " , new_section)
                inputs = self.tokenizer([new_section], return_tensors="pt", padding=True, truncation=True).to(self.device)
                outputs = self.model(**inputs)
                new_section_embedding = self.mean_pooling(outputs, inputs['attention_mask']).detach().cpu().numpy()
                print("shape" , new_section_embedding.shape)

            D, I = self.index.search(new_section_embedding, self.k)

            print("i" , I)
            mapped_sections = []
            for idx in I[0]:
                if idx != -1:
                    section = self.faiss_to_section_map.get(idx , "")
                    if section:
                        mapped_sections.append(section)

        except Exception as e:
             print(f"Error eretrive embedding: {e}") 

        return mapped_sections

# You can also add any additional methods for testing, for example:
def create_embedding_search_instance():
    return EmbeddingSearch()