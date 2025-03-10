from langchain_core.retrievers import BaseRetriever
from langchain.schema import Document
from typing import List, Any
import json
from pydantic import Field

class CouchbaseRetriever(BaseRetriever):
    """
    Retriever that uses both N1QL and vector search in Couchbase.
    """
    
    # Define fields properly for Pydantic model
    capella_client: Any = Field(description="Couchbase Capella client")
    embedding_generator: Any = Field(description="Embedding generator")
    collection_name: str = Field(default="travel-sample.inventory.landmark", description="Collection name")
    
    def __init__(self, capella_client, embedding_generator, collection_name="inventory.landmark"):
        # If collection_name doesn't include the bucket name, add it
        if collection_name.count('.') == 1:
            collection_name = f"{capella_client.bucket_name}.{collection_name}"
        
        # Initialize with proper field names for Pydantic
        super().__init__(
            capella_client=capella_client,
            embedding_generator=embedding_generator,
            collection_name=collection_name
        )
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """
        Get documents relevant to the query using both keyword and vector search.
        """
        # Generate embedding for the query
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Perform vector search
        vector_results = self._vector_search(query, query_embedding)
        
        # Perform keyword search
        keyword_results = self._keyword_search(query)
        
        # Combine and deduplicate results
        all_results = {}
        
        # Add vector search results
        for doc in vector_results:
            doc_id = doc.metadata.get("id")
            if doc_id:
                all_results[doc_id] = doc
                
        # Add keyword search results
        for doc in keyword_results:
            doc_id = doc.metadata.get("id")
            if doc_id and doc_id not in all_results:
                all_results[doc_id] = doc
                
        return list(all_results.values())
    
    def _vector_search(self, query: str, query_embedding: List[float]) -> List[Document]:
        """
        Search using vector similarity.
        """
        # Parse the collection name if it contains dots
        if "." in self.collection_name:
            parts = self.collection_name.split(".")
            if len(parts) == 3:
                bucket, scope, collection = parts
                collection_ref = f"`{bucket}`.`{scope}`.`{collection}`"
            else:
                collection_ref = f"`{self.collection_name}`"
        else:
            collection_ref = f"`{self.collection_name}`"

        vector_query = f"""
        SELECT META().id as id, landmark.* 
        FROM {collection_ref} as landmark
        WHERE SEARCH(landmark, {{
            "query": {{
                "vector_search": {{
                    "vector": {json.dumps(query_embedding)},
                    "field": "embedding",
                    "k": 3
                }}
            }}
        }})
        """
        
        try:
            results = self.capella_client.query(vector_query)
            documents = []
            
            for row in results:
                # get document content
                doc_id = row.get("id")
                content = {k: v for k, v in row.items() if k != "id"}
                
                # Create a LangChain Document
                documents.append(
                    Document(
                        page_content=str(content),
                        metadata={"id": doc_id, "source": "vector_search"}
                    )
                )
            
            return documents
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    def _keyword_search(self, query: str) -> List[Document]:
        """
        Search using N1QL keywords.
        """
        # Parse the collection name if it contains dots
        if "." in self.collection_name:
            parts = self.collection_name.split(".")
            if len(parts) == 3:
                bucket, scope, collection = parts
                collection_ref = f"`{bucket}`.`{scope}`.`{collection}`"
            else:
                collection_ref = f"`{self.collection_name}`"
        else:
            collection_ref = f"`{self.collection_name}`"

        # Get potential keywords from the query
        keywords = query.lower().split()
        keywords = [k for k in keywords if len(k) > 3]  # Filter out short words
        
        if not keywords:
            return []
        
        # find documents that contain any of the keywords within any fields
        conditions = []
        for keyword in keywords:
            conditions.append(f"LOWER(landmark.content) LIKE '%{keyword}%'")
            conditions.append(f"LOWER(landmark.name) LIKE '%{keyword}%'")
            conditions.append(f"LOWER(landmark.city) LIKE '%{keyword}%'")
            conditions.append(f"LOWER(landmark.country) LIKE '%{keyword}%'")
            
        where_clause = " OR ".join(conditions)
        
        n1ql_query = f"""
        SELECT META().id as id, landmark.* 
        FROM {collection_ref} as landmark
        WHERE {where_clause}
        LIMIT 5
        """
        
        try:
            results = self.capella_client.query(n1ql_query)
            documents = []
            
            for row in results:
                # Extract the document content
                doc_id = row.get("id")
                content = {k: v for k, v in row.items() if k != "id"}
                
                # Create a LangChain Document
                documents.append(
                    Document(
                        page_content=str(content),
                        metadata={"id": doc_id, "source": "keyword_search"}
                    )
                )
            
            return documents
        except Exception as e:
            print(f"Keyword search error: {e}")
            return []

    def retrieve_relevant_documents(self, query_text, collection_name="vectors", top_k=3):
        """
        Retrieve relevant documents based on vector similarity.
        
        Args:
            query_text (str): The query text
            collection_name (str): The collection to search in (default: vectors)
            top_k (int): Number of results to return
            
        Returns:
            list: List of relevant documents
        """
        # Generate embedding for the query
        query_embedding = self.embedding_generator.generate_embedding(query_text)
        
        # Perform vector search using the vectors collection in inventory scope
        query = f"""
        SELECT v.doc_id, l.*, ARRAY_DISTANCE(v.embedding, $embedding) AS distance
        FROM `{self.capella_client.bucket_name}`.`inventory`.`{collection_name}` AS v
        JOIN `{self.capella_client.bucket_name}`.`inventory`.`landmark` AS l
        ON v.doc_id = META(l).id
        WHERE v.embedding IS NOT MISSING
        ORDER BY distance
        LIMIT {top_k}
        """
        
        try:
            result = self.capella_client.cluster.query(
                query,
                QueryOptions(named_parameters={'embedding': query_embedding})
            )
            
            return list(result)
        except Exception as e:
            print(f"Vector search error: {e}")
            # Fall back to keyword search if vector search fails
            return self._keyword_search(query_text) 