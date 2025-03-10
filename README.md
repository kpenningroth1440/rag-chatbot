# How this works

1. Data Preparation: We add embeddings, i.e. "numbers with meaning"` to each document in the database.
2. Chatbot: You ask a question to the chatbot, e.g., "What is the capital of France?"
3. The chatbot will use the question to retrieve the most relevant documents from the database, using vector search and full text search (N1QL). It will find embeddings that are most similar to the question's embedding. It will also find documents that contain keywords which most closely match the question's keywords.
4. The chatbot will then use the retrieved documents to generate a response, after formatting into a readable answer.
5. The response is then displayed to the user.
   
# Setup
1. Clone the repository
2. Create a .env file in the root directory and add the following variables with your own values for your Capella cluster.
   - DEV_CAPELLA_ENDPOINT
   - DEV_CAPELLA_ADMIN_USER
   - DEV_CAPELLA_ADMIN_PASSWORD
   - DEV_CAPELLA_BUCKET_NAME
3. Install docker if not installed
4. Run `docker compose up --build`

# How to run the application
