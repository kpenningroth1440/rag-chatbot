# How this works

1. Data Preparation: We add embeddings, i.e. "numbers with meaning"` to each document in the database.
2. Chatbot: You ask a question to the chatbot, e.g., "What is the capital of France?"
3. The chatbot will use the question to retrieve the most relevant documents from the database, using Capella vector search and Capella full text search if needed or desired. The chatbot will find embeddings that are most similar to the question's embedding. It can also find documents that contain keywords which most closely match the question's keywords, if the user desires.
4. The chatbot will then use the retrieved documents to generate a response, after formatting into a readable answer.
5. The response is then displayed to the user.

## Quick Setup with Shell/Batch Scripts

### Prerequisites

- Python 3.10 or higher: https://www.python.org/downloads/
- Couchbase Capella Community Edition Account
  - Make sure to start a free Capella cluster: https://cloud.couchbase.com/sign-up
  - Add the credentials (see below) to the cluster access credentials in the Capella UI, you will specify these.
  - Add your computer's IP address to the allowed IP addresses in the Capella UI
  - IMPORTANT:
     - If you are using a VPN, you need to add the VPN's IP address to the allowed IP addresses in the Capella UI. Also, if you switch networks, 
       you need to add your new IP address to the allowed IP addresses in the Capella UI.
     - The chatbot will create the schema for the vectors collection, but you will need to
       create the vector index. Make sure to use the "embedding" field for indexing in the vectors collection. You can run the chatbot up until         the collection is created (your terminal will print this), but once that's done create the index, then proceed in your terminal.
        - https://docs.couchbase.com/cloud/vector-search/vector-search.html
     - You will need to create the full text search index yourself in Capella UI. You will want to use the same fields as this project does
       if you want this code to work as is. I utilized the "landmark" collection for this project. The keyword search option within the chatbot 
       will not work until this is done.
     - For the index names, I used:
        - landmarks-vector-index (INDEX FOR VECTOR SEARCH)
        - landmarks-text-index (INDEX FOR FULL TEXT SEARCH)

### Setup Instructions

#### Create project folder (ex. rag-chatbot) and clone this repo into it:

   ```bash
   git clone https://github.com/couchbaselabs/rag-chatbot.git
   ```

#### Create a `.env` file in the root of the project folder with your Couchbase Capella credentials:

   - DEV_CAPELLA_ENDPOINT
   - DEV_CAPELLA_ADMIN_USER
   - DEV_CAPELLA_ADMIN_PASSWORD
   - DEV_CAPELLA_BUCKET_NAME

#### Run the setup script, make sure to run it from the root of the project folder:

  ##### On Mac/Linux:

  ```bash
  # Make scripts executable
  chmod +x setup.sh run.sh
  
  # Run the setup script
  ./setup.sh
  ```

  ##### On Windows:
  
  ```bash
  # Run the setup script
  setup.bat
  ```

#### Run the application:

  ##### On Mac/Linux:
  
  ```bash
  ./run.sh
  ```
  
  ##### On Windows:
  
  ```bash
  run.bat
  ```

The setup scripts will:

  - Create a virtual environment
  - Activate the virtual environment
  - Install all required dependencies

The run scripts will:

  - Activate the virtual environment if not already activated
  - Start the chatbot application
