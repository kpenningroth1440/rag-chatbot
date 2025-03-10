from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import json

class EmbeddingGenerator:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initialize the embedding generator with a specific model.
        """
        self.model = SentenceTransformer(model_name)
        self.vector_dimension = self.model.get_sentence_embedding_dimension()
        print(f"Loaded embedding model: {model_name} with dimension {self.vector_dimension}")
        
    def generate_embedding(self, text):
        """
        Generate an embedding vector for the given text.
        An embedding is a vector (numeric) representation of the text.
        It can be used to compare the text to other texts.
        """
        if not text:
            return None
            
        # Generate embedding and convert to list for storage in Couchbase
        embedding = self.model.encode(text)
        return embedding.tolist() 

    def store_embedding(self, client, doc_id, text, scope_name="inventory", collection_name="vectors"):
        """
        Store an embedding in the vectors collection.
        
        Args:
            client: Couchbase client
            doc_id (str): ID of the original document
            text (str): Text to generate embedding for
            scope_name (str): Scope name (default: inventory)
            collection_name (str): Collection name (default: vectors)
            
        Returns:
            bool: Success status
        """
        try:
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Create vector document
            vector_doc = {
                "doc_id": doc_id,
                "embedding": embedding,
                "text": text,
                "created_at": datetime.now().isoformat()
            }
            
            # Try to get the vectors collection
            try:
                # First try to access the collection directly
                vectors_collection = client.bucket.scope(scope_name).collection(collection_name)
                
                # Store the vector document with a unique ID
                vector_id = f"vector::{doc_id}"
                vectors_collection.upsert(vector_id, vector_doc)
                
                return True
            except Exception as e:
                # If that fails, try using a query instead
                print(f"Direct collection access failed: {e}")
                print("Trying to insert via query...")
                
                query = f"""
                INSERT INTO `{client.bucket_name}`.`{scope_name}`.`{collection_name}`
                (KEY, VALUE)
                VALUES ('vector::{doc_id}', {json.dumps(vector_doc)})
                """
                
                client.cluster.query(query)
                return True
                
        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False 