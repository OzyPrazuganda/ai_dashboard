import pandas as pd
import numpy as np
import faiss
import os
import time
from sentence_transformers import SentenceTransformer
from multiprocessing import Pool, cpu_count
import pickle

class ChatbotOptimized:
    def __init__(self, model_name='cahya/distilbert-base-indonesian', index_dir='chatbot_index'):
        self.model_name = model_name
        self.index_dir = index_dir
        self.model = None
        self.questions = []
        self.answers = []
        self.index = None
        
    def load_data(self, file_path):
        df = pd.read_csv(file_path)
        
        for _, row in df.iterrows():
            answer = row['NEW - ANSWER'] if pd.notna(row['NEW - ANSWER']) else row['ID Answer']
            
            if pd.notna(row['ID Example']):
                self.questions.append(row['ID Example'])
                self.answers.append(answer)
            
            for i in range(1, 11):
                col_name = f'ID Pertanyaan Serupa {i}-ID'
                if pd.notna(row[col_name]) and row[col_name] != 'Null':
                    self.questions.append(row[col_name])
                    self.answers.append(answer)
        
        print(f"Loaded {len(self.questions)} questions with answers")
    
    def _generate_embeddings_parallel(self, texts, batch_size=128):
        """Generate embeddings using parallel processing"""
        # Create batches
        batches = [texts[i:i+batch_size] for i in range(0, len(texts), batch_size)]
        
        with Pool(processes=cpu_count()) as pool:
            results = pool.map(self.model.encode, batches)
        return np.vstack(results)
    
    def build_index(self):
        start_time = time.time()
        
        self.model = SentenceTransformer(self.model_name)
        print(f"Model loaded in {time.time() - start_time:.2f}s")
        
        embedding_time = time.time()
        question_embeddings = self._generate_embeddings_parallel(
            self.questions, 
            batch_size=128
        )
        print(f"Embeddings generated in {time.time() - embedding_time:.2f}s")
        
        index_time = time.time()
        dimension = question_embeddings.shape[1]
        
        nlist = 100
        quantizer = faiss.IndexFlatIP(dimension)
        self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
        
        faiss.normalize_L2(question_embeddings)
        
        self.index.train(question_embeddings)
        self.index.add(question_embeddings)
        self.index.nprobe = 10  # Number of clusters to search
        
        print(f"Index built in {time.time() - index_time:.2f}s")
        print(f"Total build time: {time.time() - start_time:.2f}s")
    
    def save_index(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
        
        faiss.write_index(self.index, os.path.join(self.index_dir, "index.faiss"))
        
        with open(os.path.join(self.index_dir, "metadata.pkl"), "wb") as f:
            pickle.dump({
                'questions': self.questions,
                'answers': self.answers,
                'model_name': self.model_name
            }, f)
        
        print(f"Index saved to {self.index_dir}")
    
    def load_index(self):
        self.index = faiss.read_index(os.path.join(self.index_dir, "faiss.index"))
        
        with open(os.path.join(self.index_dir, "metadata.pkl"), "rb") as f:
            metadata = pickle.load(f)
            self.questions = metadata['questions']
            self.answers = metadata['answers']
            model_name = metadata['model_name']
        
        if model_name != self.model_name:
            print(f"Warning: Saved model ({model_name}) differs from requested model ({self.model_name})")
        self.model = SentenceTransformer(model_name)
        
        print(f"Loaded index with {len(self.questions)} questions")
    
    def query(self, question, k=3, threshold=0.9):
        """Search for similar questions with similarity threshold"""
        query_embedding = self.model.encode([question], normalize_embeddings=True)
        faiss.normalize_L2(query_embedding)
        
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            similarity = distances[0][i]
            
            if idx < 0 or similarity < threshold:
                continue
                
            results.append({
                'question': self.questions[idx],
                'answer': self.answers[idx],
                'similarity': similarity
            })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results