from langchain_core.retrievers import BaseRetriever
from langchain.schema import Document
from typing import List
import couchbase.search as search
from couchbase.options import SearchOptions
from couchbase.vector_search import VectorQuery, VectorSearch
import json
from pydantic import Field
from db.capella_client import CapellaClient
from rag.embeddings import EmbeddingGenerator

class CouchbaseRetriever(BaseRetriever):
    """
    Document retriever that can use both FTS (Full Text Search)
    and vector search w/ Couchbase Capella.
    """
    capella_client: CapellaClient = Field(default=None)
    embedding_generator: EmbeddingGenerator = Field(default=None)
    vector_search_index_name: str = Field(default="")
    text_search_index_name: str = Field(default="")
    collection_name: str = Field(default="")
    # if vector search is used, the number of candidates to return
    # if keyword search is used, the number of candiates will double
    num_candidates: int = 3
    keyword_search: bool = True
    
    def __init__(self, capella_client, embedding_generator, vector_search_index_name, collection_name, num_candidates, keyword_search, text_search_index_name=None):
        # Add bucket name to collection name if not provided
        if collection_name.count('.') == 1:
            collection_name = f"{capella_client.bucket_name}.{collection_name}"
        
        # initialize LangChain BaseRetriever, the parent class
        super().__init__()
        
        # Store parameters
        self.capella_client = capella_client
        self.embedding_generator = embedding_generator
        self.collection_name = collection_name
        self.vector_search_index_name = vector_search_index_name
        self.num_candidates = num_candidates
        self.keyword_search = keyword_search
        self.text_search_index_name = text_search_index_name
    
    def _ensure_connection(self):
        """
        Ensure the connection to Couchbase is active, reconnect if needed.
        """
        try:
            # Try a simple operation to check connection
            self.capella_client.cluster.ping()
        except Exception as e:
            print(f"Connection error: {e}. Attempting to reconnect...")
            try:
                # Reconnect with the same parameters
                self.capella_client.connect(timeout_seconds=15, apply_wan_profile=True)
                print("Successfully reconnected to Couchbase")
            except Exception as reconnect_error:
                print(f"Failed to reconnect: {reconnect_error}")
                raise
    
    def _keyword_search(self, query: str) -> List[Document]:
        """
        Search using Full Text Search (FTS) capabilities of Capella with scoped indexes.
        """
        try:
            # Force reconnection to ensure a fresh connection
            try:
                self.capella_client.connect(timeout_seconds=15, apply_wan_profile=True)
                print("Successfully reconnected to Couchbase")
            except Exception as reconnect_error:
                print(f"Reconnection warning (continuing anyway): {reconnect_error}")
            
            bucket = self.capella_client.cluster.bucket(self.capella_client.bucket_name)
            scope = bucket.scope("inventory")
            
            search_options = SearchOptions(
                limit=self.num_candidates,
                fields=["activity", "city", "content", "country", "name", "state", "title", "type"]
            )

            # Create a disjunction query to match any field
            field_queries = [
                search.MatchQuery(query, field="name"),
                search.MatchQuery(query, field="content"),
                search.MatchQuery(query, field="activity"),
                search.MatchQuery(query, field="title"),
                search.MatchQuery(query, field="city"),
                search.MatchQuery(query, field="country"),
                search.MatchQuery(query, field="state"),
                search.MatchQuery(query, field="type")
            ]
            
            # Combine queries with OR logic - unpack the list with *
            request = search.SearchRequest.create(
                search.DisjunctionQuery(*field_queries)
            )
            result = scope.search(
                self.text_search_index_name,
                request,
                search_options
            )
            rows = list(result.rows())
            print(f"Found {len(rows)} potential matches in keyword search...")
            documents = []
            for row in rows:
                doc_id = row.id
                # Extract fields with proper error handling
                fields = row.fields if hasattr(row, 'fields') else {}
                content = {
                    "id": doc_id,
                    "name": fields.get("name", ""),
                    "content": fields.get("content", ""),
                    "country": fields.get("country", ""),
                    "city": fields.get("city", ""),
                    "type": fields.get("type", ""),
                    "activity": fields.get("activity", "")
                }
                documents.append(
                    Document(
                        page_content=json.dumps(content),
                        metadata={
                            "id": doc_id,
                            "source": "keyword_search",
                            "score": row.score if hasattr(row, 'score') else 0
                        }
                    )
                )
            
            return documents
            
        except Exception as e:
            print(f"Full text search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_relevant_documents(self, prompt: str) -> List[Document]:
        """
        Get documents relevant to the query using vector search
        and keyword search.
        
        Keyword search is used as a fallback if vector search
        doesn't return any results, or if the user wants to use both.
        """
        # Check if cappella cluster connection is still active and reconnect if needed
        self._ensure_connection()
        # Generate embedding from the query
        query_embedding = self.embedding_generator.generate_embedding(prompt)
        all_results = {}
        score_results = {}
        vector_doc_ids = []
        try:
            # STEP 1: Perform vector search to get relevant document IDs
            scope = self.capella_client.cluster.bucket(self.capella_client.bucket_name).scope("inventory")
            # Create the search request, increase num_candidates if you want more results
            search_req = search.SearchRequest.create(search.MatchNoneQuery()).with_vector_search(
                VectorSearch.from_vector_query(
                    VectorQuery('embedding', query_embedding, num_candidates=self.num_candidates)
                )
            )
            # NOTE: DOCUMENT FIELDS ARE ONLY RETURNED 
            # IF THEY ARE INCLUDED IN THE SEARCH INDEX
            search_options = SearchOptions(limit=10, fields=["*"])
            result = scope.search(
                self.vector_search_index_name,
                search_req, 
                search_options
            )
            # Get document IDs from vector search results
            for row in result.rows():
                doc_id = row.id
                if doc_id and doc_id.startswith("vector::"):
                    try:
                        original_doc_id = doc_id.replace("vector::", "")
                        vector_doc_ids.append(original_doc_id)
                        score_results[original_doc_id] = row.score
                    except Exception as e:
                        print(f"Error extracting document ID from {doc_id}: {e}")
            # STEP 2: Fetch the landmark documents using the IDs
            if vector_doc_ids:
                # Create IN clause for the document IDs
                doc_ids_str = ", ".join([f"'{doc_id}'" for doc_id in vector_doc_ids])
                query = f"""
                SELECT META().id as id, l.*
                FROM `{self.capella_client.bucket_name}`.inventory.landmark AS l
                WHERE META().id IN [{doc_ids_str}]
                """
                landmark_results = self.capella_client.execute_query(query)
                for row in landmark_results:
                    doc_id = row.get("id")
                    # Extract the landmark data from the nested 'l' field
                    if 'l' in row:
                        content = row['l']
                    else:
                        # Remove 'id' field
                        content = {k: v for k, v in row.items() if k != "id"}
                    # Create a LangChain Document
                    all_results[doc_id] = Document(
                        page_content=json.dumps(content),
                        metadata={"id": doc_id, "source": "vector_search", "score": score_results.get(f"landmark_{doc_id}", 0)}
                    )
        except Exception as e:
            print(f"Vector search error: {str(e)}")
        # Perform keyword search as a fallback, 
        # or if user wants to use both keyword and vector search
        if not all_results or len(all_results) != self.num_candidates or self.keyword_search:
            print("Performing keyword search...")
            keyword_results = self._keyword_search(prompt)
            for doc in keyword_results:
                doc_id = doc.metadata.get("id")
                doc_id = int(doc_id.split(f"{self.collection_name}_")[1])
                # don't need to duplicate ids
                if doc_id not in all_results:
                    all_results[doc_id] = doc
                else:
                    print(f"Match was already found during vector embeddingsearch: {doc_id}")
        
        return list(all_results.values())