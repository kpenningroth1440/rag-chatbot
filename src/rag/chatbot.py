from langchain.chains import RetrievalQA
from langchain_community.llms import FakeListLLM

class TravelChatbot:
    """
    A chatbot for answering travel-related questions,
    based off the travel-sample dataset.
    """
    
    def __init__(self, retriever):
        self.retriever = retriever
        # Since we're not using an actual LLM API, we'll use a fake LLM
        # In a real implementation, you would use an actual LLM like OpenAI
        self.llm = FakeListLLM(responses=["I'll format the retrieved information for you."])
        
        # Create a QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True
        )
        
    def answer_question(self, question):
        """
        Answer a user question using the retrieval system.
        """
        # Get the raw result from QA chain
        result = self.qa_chain({"query": question})
        
        # Extract documents
        source_docs = result.get("source_documents", [])
        
        if not source_docs:
            return "I couldn't find any information related to your question. Could you try asking in a different way?"
        
        # Format response
        response = "Here's what I found regarding your question:\n\n"
        
        for i, doc in enumerate(source_docs[:3], 1):  # Limit to top 3 results
            content = doc.page_content
            try:
                # Parse content
                if isinstance(content, str) and content.startswith("{"):
                    import ast
                    content_dict = ast.literal_eval(content)
                    
                    # Format information
                    response += f"#{i} {content_dict.get('name', 'Unknown Landmark')}\n"
                    if "country" in content_dict:
                        response += f"Location: {content_dict.get('city', '')}, {content_dict.get('country', '')}\n"
                    if "content" in content_dict:
                        response += f"Description: {content_dict.get('content', '')}\n"
                else:
                    response += f"#{i} {content}\n"
            except:
                # Fallback to raw content if parsing fails
                response += f"#{i} {content}\n"
            
            response += f"Source: {doc.metadata.get('source', 'Unknown')}\n\n"
        
        return response 