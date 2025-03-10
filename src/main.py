import os
from dotenv import load_dotenv
from db.capella_client import CapellaClient
from rag.embeddings import EmbeddingGenerator
from rag.retriever import CouchbaseRetriever
from rag.chatbot import TravelChatbot
from data.travel_sample_loader import TravelSampleLoader
import time

def main():
    print("Starting Travel Chatbot...")
    
    load_dotenv()
    print("Environment variables loaded.")
    
    print("Getting connection details...")
    endpoint = os.getenv("DEV_CAPELLA_ENDPOINT")
    username = os.getenv("DEV_CAPELLA_ADMIN_USER")
    password = os.getenv("DEV_CAPELLA_ADMIN_PASSWORD")
    bucket_name = "travel-sample"
    print(f"Endpoint: {endpoint}")
    print(f"Username: {username}")
    print(f"Password: {'*' * (len(password) if password else 0)}")
    print(f"Bucket: {bucket_name}")
    
    if not all([endpoint, username, password, bucket_name]):
        print("Error: Missing required environment variables.")
        return
    
    try:
        print(f"Connecting to Couchbase Capella at {endpoint}...")
        
        client = CapellaClient(
            endpoint=endpoint,
            username=username,
            password=password,
            bucket_name=bucket_name
        )
        print("Client created, connecting...")
    
        try:
            if client.connect(timeout_seconds=15, apply_wan_profile=True):
                print("Successfully connected to Couchbase Capella!")
                
                # Create necessary collections for RAG
                print("Setting up collections for RAG system...")
                
                # Use the existing inventory scope
                try:
                    # Check if vectors collection exists in inventory scope
                    try:
                        client.bucket.scope("inventory").collection("vectors")
                        print("Vectors collection already exists in inventory scope")
                    except Exception:
                        # Create vectors collection in inventory scope
                        client.cluster.query(f"CREATE COLLECTION `{bucket_name}`.inventory.vectors IF NOT EXISTS")
                        print("Created vectors collection in inventory scope")
                        time.sleep(2)  # Wait for collection to be available
                except Exception as e:
                    print(f"Error setting up collections: {e}")
                
                print("Collections setup complete")
        except Exception as e:
            print(f"Connection failed: {e}")
            print("This could be due to network issues, firewall settings, or VPN configuration.")
            print("Check if your endpoint format is correct (should NOT include protocol prefix).")
            raise
        
        print("Initializing embedding model...")
        embedding_generator = EmbeddingGenerator()
        
        prepare_data = input("Do you want to prepare the travel-sample data? (y/n): ").lower() == 'y'
        
        if prepare_data:
            print("Preparing travel-sample data...")
            loader = TravelSampleLoader(client, embedding_generator)
            
            print("Checking for existing embeddings...")
            existing_count = loader.check_existing_embeddings()
            
            if existing_count > 0:
                proceed = input(f"Found {existing_count} existing embeddings. Regenerate them? (y/n): ").lower() == 'y'
                if not proceed:
                    print("Skipping embedding generation")
                else:
                    print("Adding embeddings to landmarks...")
                    loader.add_embeddings_to_vectors_collection()
            else:
                print("No existing embeddings found. Adding embeddings to landmarks...")
                loader.add_embeddings_to_vectors_collection()
        
        print("Initializing retriever and chatbot...")
        retriever = CouchbaseRetriever(client, embedding_generator)
        chatbot = TravelChatbot(retriever)
        
        print("\n=== Travel Information Chatbot ===")
        print("Ask questions about landmarks, cities, or countries.")
        print("Type 'exit' to quit.")
        print("================================\n")
        
        while True:
            user_input = input("\nYour question: ")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Goodbye!")
                break
                
            if not user_input.strip():
                continue
                
            # Get the answer
            answer = chatbot.answer_question(user_input)
            print("\n" + answer)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 