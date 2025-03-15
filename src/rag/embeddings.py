from sentence_transformers import SentenceTransformer
from datetime import datetime
import json

class EmbeddingGenerator:
    """
    Generates vectorembeddings from text using langchain 
    and a pre-trained model.
    """
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)
        self.vector_dimension = self.model.get_sentence_embedding_dimension()
        print(f"Loaded embedding model: {model_name} with dimension {self.vector_dimension}")
        
    def generate_embedding(self, text):
        """
        Generate an embedding vector for the given text.
        The embedding is a vector (numeric) representation of the text.
        It can be used to compare the text to other texts.
        """
        if not text:
            return None
        
        embedding = self.model.encode(text)
        # arrays are not JSON serializable, so we convert to list
        return embedding.tolist()

    def store_embedding(self, client, doc_id, text, scope_name, collection_name):
        """
        Store a vector embedding in the specified collection.
        """
        try:
            embedding = self.generate_embedding(text)
            # Create vector document
            vector_doc = {
                "doc_id": doc_id,
                "embedding": embedding,
                "created_at": datetime.now().isoformat()
            }
            # Try to get the specified collection
            try:
                vectors_collection = client.bucket.scope(scope_name).collection(collection_name)
                # Store the vector document with a unique ID
                vector_id = f"vector::{doc_id}"
                vectors_collection.upsert(vector_id, vector_doc)
                return True
            except Exception as e:
                print(f"Capella collection access failed, make sure the collection exists: {e}")
                print("Trying to insert via query...")
                # If Capella collection access fails, try to insert via query
                query = f"""
                INSERT INTO `{client.bucket_name}`.`{scope_name}`.`{collection_name}`
                (KEY, VALUE)
                VALUES ('vector::{doc_id}', {json.dumps(vector_doc)})
                """
                client.cluster.execute_query(query)
                return True
                
        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False 