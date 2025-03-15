

class TravelSampleLoader():
    """
    Utility to load/prepare travel-sample data for chatbot.
    """
    
    def __init__(self, capella_client, embedding_generator):
        self.client = capella_client
        self.embedding_generator = embedding_generator

    def add_embeddings_to_vectors_collection(self):
        """Add embeddings to the vectors collection for all landmarks."""
        try:
            # get all landmark document results to embed
            query = """
            SELECT META().id as id, l.name, l.content, l.country, l.city, l.type, l.activity
            FROM `travel-sample`.inventory.landmark AS l
            """
            # convert results to a list
            # to avoid "already iterated" error
            results = list(self.client.execute_query(query))
            count = 0
            for row in results:
                doc_id = row.get("id")
                text_for_embedding = f"{row.get('name', '')} {row.get('content', '')} {row.get('country', '')} {row.get('city', '')} {row.get('type', '')} {row.get('activity', '')}"
                try:
                    # store embedding in vectors collection
                    if self.embedding_generator.store_embedding(
                        self.client, 
                        doc_id, 
                        text_for_embedding,
                        scope_name="inventory",
                        collection_name="vectors"
                    ):
                        count += 1
                        
                    if count % 100 == 0:
                        print(f"Added {count} embeddings...")
                except Exception as e:
                    print(f"Error storing embedding for {doc_id}: {e}")
            
            print(f"Successfully added embeddings for {count} landmarks")
            return True
        except Exception as e:
            print(f"Error adding embeddings to vectors collection: {e}")
            return False


    def check_existing_embeddings(self):
        """Check if embeddings already exist in the vectors collection."""
        try:
            # Count documents in the vectors collection
            query = """
            SELECT COUNT(*) as count
            FROM `travel-sample`.inventory.vectors
            """
            result = self.client.execute_query(query)
            count = result[0].get('count', 0)
            return count
        except Exception as e:
            print(f"Error checking existing embeddings: {e}")
            return 0 