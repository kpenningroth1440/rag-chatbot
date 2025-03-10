from rag.embeddings import EmbeddingGenerator
import time

class TravelSampleLoader:
    """
    Utility to load/prepare travel-sample data for chatbot.
    """
    
    def __init__(self, capella_client, embedding_generator):
        self.client = capella_client
        self.embedding_generator = embedding_generator
        
    def create_indexes(self):
        """Create necessary indexes for the RAG system."""
        try:
            # Create index for vector search in the vectors collection
            vector_index_query = """
            CREATE INDEX idx_vectors_embedding ON `travel-sample`.inventory.vectors(embedding) 
            USING GSI
            WITH {"defer_build": true}
            """
            self.client.cluster.query(vector_index_query)
            print("Created vector embedding index")
            
            # Build the index
            build_index_query = """
            BUILD INDEX ON `travel-sample`.inventory.vectors(idx_vectors_embedding)
            """
            self.client.cluster.query(build_index_query)
            print("Built vector embedding index")
            
            return True
        except Exception as e:
            print(f"Error creating indexes: {e}")
            return False

    def add_embeddings_to_vectors_collection(self):
        """Add embeddings to the vectors collection for all landmarks."""
        try:
            # First ensure the vectors collection exists
            try:
                self.client.cluster.query(f"CREATE COLLECTION `{self.client.bucket_name}`.inventory.vectors IF NOT EXISTS")
                print("Confirmed 'vectors' collection exists in inventory scope")
                
                # Wait a moment for the collection to be available
                import time
                time.sleep(2)
            except Exception as e:
                print(f"Note when creating collection: {e}")
            
            # Query to get all landmarks
            query = """
            SELECT META().id as id, l.name, l.content, l.country, l.city
            FROM `travel-sample`.inventory.landmark AS l
            LIMIT 100
            """
            
            results = self.client.query(query)
            
            count = 0
            for row in results:
                doc_id = row.get("id")
                
                # Combine relevant fields for embedding
                text_for_embedding = f"{row.get('name', '')} {row.get('content', '')} {row.get('country', '')} {row.get('city', '')}"
                
                try:
                    # Store the embedding in inventory.vectors
                    if self.embedding_generator.store_embedding(
                        self.client, 
                        doc_id, 
                        text_for_embedding,
                        scope_name="inventory"
                    ):
                        count += 1
                        
                    # Print progress
                    if count % 10 == 0:
                        print(f"Added {count} embeddings...")
                except Exception as e:
                    print(f"Error storing embedding for {doc_id}: {e}")
            
            print(f"Successfully added embeddings for {count} landmarks")
            return True
        except Exception as e:
            print(f"Error adding embeddings: {e}")
            return False

    def add_embeddings_to_landmarks(self, limit=100):
        """
        Add embeddings to landmark documents.
        """
        try:
            # Query landmarks without embeddings
            query = f"""
            SELECT META().id as id, l.name, l.content
            FROM `travel-sample`.inventory.landmark l
            WHERE l.embedding IS MISSING
            LIMIT {limit}
            """
            
            results = self.client.query(query)
            
            count = 0
            for row in results:
                doc_id = row.get("id")
                name = row.get("name", "")
                content = row.get("content", "")
                
                text_to_embed = f"{name}. {content}"
                
                embedding = self.embedding_generator.generate_embedding(text_to_embed)
                
                if embedding:
                    # update document with embedding
                    update_query = f"""
                    UPDATE `travel-sample`.inventory.landmark
                    SET embedding = $embedding
                    WHERE META().id = $id
                    """
                    
                    self.client.query(
                        update_query, 
                        named_parameters={"embedding": embedding, "id": doc_id}
                    )
                    
                    count += 1
                    if count % 10 == 0:
                        print(f"Processed {count} documents")
                        time.sleep(0.5)
            
            print(f"Added embeddings to {count} landmark documents")
            
        except Exception as e:
            print(f"Error adding embeddings: {e}") 

    def check_existing_embeddings(self):
        """Check if embeddings already exist in the vectors collection."""
        try:
            # Count documents in the vectors collection
            query = """
            SELECT COUNT(*) as count
            FROM `travel-sample`.inventory.vectors
            """
            
            result = self.client.query(query)
            count = next(result).get('count', 0)
            
            print(f"Found {count} existing embeddings in the vectors collection")
            return count
        except Exception as e:
            print(f"Error checking existing embeddings: {e}")
            return 0 