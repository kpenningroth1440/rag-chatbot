# How this works

1. Data Preparation: We add embeddings, i.e. "numbers with meaning"` to each document in the database.
2. Chatbot: You ask a question to the chatbot, e.g., "What is the capital of France?"
3. The chatbot will use the question to retrieve the most relevant documents from the database, using vector search and full text search (N1QL) if needed or desired. It will find embeddings that are most similar to the question's embedding. It will also find documents that contain keywords which most closely match the question's keywords.
4. The chatbot will then use the retrieved documents to generate a response, after formatting into a readable answer.
5. The response is then displayed to the user.

## Quick Setup with Shell/Batch Scripts

### Prerequisites

- Python 3.10 or higher: https://www.python.org/downloads/
- Couchbase Capella Community Edition Account
- - Make sure to start a free Capella cluster: https://cloud.couchbase.com/sign-up
- - Add the credentials to the cluster access credentials in the Capella UI
- - Add your computer's IP address to the allowed IP addresses in the Capella UI
- - NOTE: If you are using a VPN, you need to add the VPN's IP address to the allowed IP addresses in the Capella UI. Also, if you switch networks, you need to add your new IP address to the allowed IP addresses in the Capella UI.

### Setup Instructions

1. Create project folder (ex. rag-chatbot) and clone this repo into it:

   git clone https://github.com/couchbaselabs/rag-chatbot.git

2. Create a `.env` file in the root of the project folder with your Couchbase Capella credentials:

   - DEV_CAPELLA_ENDPOINT
   - DEV_CAPELLA_ADMIN_USER
   - DEV_CAPELLA_ADMIN_PASSWORD
   - DEV_CAPELLA_BUCKET_NAME

3. Run the setup script, make sure to run it from the root of the project folder:

#### On Mac/Linux:

```bash
# Make scripts executable
chmod +x setup.sh run.sh

# Run the setup script
./setup.sh
```

#### On Windows:

```bash
# Run the setup script
setup.bat
```

4. Run the application:

#### On Mac/Linux:

```bash
./run.sh
```

#### On Windows:

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
