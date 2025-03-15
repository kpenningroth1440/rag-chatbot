import os
from dotenv import load_dotenv
from db.capella_client import CapellaClient
from rag.embeddings import EmbeddingGenerator
from rag.retriever import CouchbaseRetriever
from rag.chatbot import TravelChatbot
from data.travel_sample_loader import TravelSampleLoader
import time
import sys
import traceback
def main():
    
    print("Starting Travel Chatbot...")
    load_dotenv()
    print("Getting connection details...")
    endpoint = os.getenv("DEV_CAPELLA_ENDPOINT")
    username = os.getenv("DEV_CAPELLA_ADMIN_USER")
    password = os.getenv("DEV_CAPELLA_ADMIN_PASSWORD")
    bucket_name = os.getenv("DEV_CAPELLA_BUCKET_NAME")
    if not all([endpoint, username, password, bucket_name]):
        print("Error: Missing required environment variables.")
        return
    
    print(f"Endpoint: {endpoint}")
    print(f"Username: {username}")
    print(f"Password: {'*' * (len(password) if password else 0)}")
    print(f"Bucket: {bucket_name}")
    try:
        client = CapellaClient(
            endpoint=endpoint,
            username=username,
            password=password,
            bucket_name=bucket_name
        )
        print("connecting to capella...")
    
        try:
            client = client.connect(timeout_seconds=15, apply_wan_profile=True)
            print("Successfully connected to capella!")
            print("Setting up collections for RAG system...")
            try:
                client.create_embedding_collection("inventory", "vectors")
                time.sleep(5)  # Wait for collection to be available
            except Exception as e:
                print(f"Error setting up vector collection: {e}")

            print("Collection setup complete")
        except Exception as e:
            print(f"Connection failed: {e}")
            traceback.print_exc()
            print("Check if your endpoint format is correct (should NOT include protocol prefix).")
            raise
        # can specify any models supported here: https://www.sbert.net/docs/sentence_transformer/pretrained_models.html
        embedding_generator = EmbeddingGenerator(model_name="all-mpnet-base-v2")
        print(f"Preparing {bucket_name} data...")
        loader = TravelSampleLoader(client, embedding_generator)
        existing_count = loader.check_existing_embeddings()
        if existing_count > 0:
            user_input = input(f"Found {existing_count} existing embeddings. Regenerate them? (y/n): ").lower()
            proceed = user_input == 'y'
            if not proceed:
                print("Skipping embedding generation")
            else:
                print("Adding embeddings to vectors collection...")
                loader.add_embeddings_to_vectors_collection()
        else:
            print("No existing embeddings found. Adding embeddings to vectors collection...")
            loader.add_embeddings_to_vectors_collection()
        # ensure vector search index exists, this can be created in Capella UI: 
        #   - https://docs.couchbase.com/cloud/vector-search/create-vector-search-index-ui.html
        print("Available search indexes:")
        try:
            # Get the cluster manager
            mgr = client.cluster.search_indexes()
            # List all indexes
            for idx in mgr.get_all_indexes():
                print(f"- {idx.name}")
        except Exception as e:
            print(f"Error listing indexes: {e}")
        user_input = input(f"Do you want to use keyword search? (y/n): ").lower()
        keyword_search = user_input == 'y'
        user_input = input(f"Enter the number of potential answers to return, if you opt-in for keyword search, this value will be doubled: ")
        num_candidates = int(user_input)
        
        
        print(f"Using {num_candidates} candidates for retrieval. Keyword search: {'enabled' if keyword_search else 'disabled'}")
        retriever = CouchbaseRetriever(client, embedding_generator, vector_search_index_name="landmarks-vector-index", collection_name="landmark", num_candidates=num_candidates, keyword_search=keyword_search, text_search_index_name="landmarks-text-index")
        chatbot = TravelChatbot(retriever)
        
        print("\n=== Travel Information Chatbot ===")
        print("Ask questions about landmarks, cities, or countries.")
        print("Type 'exit' to quit.")
        print("================================\n")
        # loop to keep chatbot running
        while True:
            user_input = input("\nYour question: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
            if not user_input.strip():
                continue
            answer = chatbot.answer_question(user_input)
            print("\n" + answer)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 