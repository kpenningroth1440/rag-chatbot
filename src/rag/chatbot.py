from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import FakeListLLM
import json

class TravelChatbot:
    """
    Chatbot for answering travel-related questions
    based off the travel-sample dataset.
    Uses a fake LLM that returns documents retrieved
    by the CouchbaseRetriever in this project.
    """
    
    def __init__(self, retriever):
        """
        Initialize the chatbot with a retriever.
        Uses a fake LLM that just returns the retrieved documents.
        """
        self.retriever = retriever
        
        # Create a fake LLM that just returns formatted content
        # SOURCE: https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.fake.FakeListLLM.html
        self.llm = FakeListLLM(
            responses=["I'll format the retrieved information for you."]
        )
        system_prompt = (
            "You are a helpful travel assistant that provides information about landmarks and destinations. "
            "Use the following context to answer the user's question. "
            "If you don't know the answer based on the context, say you don't know but offer anything you know about the topic. "
            "Keep your answers concise, avoid using complex words and be helpful.\n\n"
            "Context: {context}"
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        # Create the document chain
        docs_chain = create_stuff_documents_chain(self.llm, prompt)
        # Create the retrieval chain
        self.qa_chain = create_retrieval_chain(
            self.retriever, 
            docs_chain
        )
        
    def answer_question(self, question):
        """
        Answer a travel-related question using retrieved documents.
        """
        try:
            # get answer from chain
            # behind the scenes this method invokes the retreiver's get_relevant_documents method,
            # utilizing the custom retreiver (CouchbaseRetriever) in this project,
            # this retreiver inherits from BaseRetriever, 
            # which has a get_relevant_documents method as well
            result = self.qa_chain.invoke({"input": question})
            source_docs = result.get("context", [])
            if not source_docs:
                return "I couldn't find any information related to your question. Could you try asking in a different way?"
            response = "Here's what I found regarding your question:\n\n"
            for i, doc in enumerate(source_docs, 1):
                content = doc.page_content
                if isinstance(content, dict):
                    content_dict = content
                else:
                    try:
                        content_dict = json.loads(content)
                    except Exception as e:
                        print(f"Error parsing content: {e}, content for parsing: {content}")
                        # Fallback to raw content
                        response += f"#{i} {str(content)[:100]}...\n"
                        continue
                # Format information
                response += f"#{i} {content_dict.get('name', 'Unknown Landmark')}\n"
                response += f"Source: {doc.metadata.get('source', 'Unknown')}\n"
                if "country" in content_dict:
                    response += f"Location: {content_dict.get('city', '')}, {content_dict.get('country', '')}\n"
                if "type" in content_dict:
                    response += f"Type: {content_dict.get('type', '')}\n"
                if "activity" in content_dict:
                    response += f"Activity: {content_dict.get('activity', '')}\n"
                if "content" in content_dict:
                    response += f"Description: {content_dict.get('content', '')}\n"
                response += "\n"
            
            return response
            
        except Exception as e:
            print(f"Error answering question: {e}")
            import traceback
            traceback.print_exc()
            return "I'm having trouble answering that question right now. Could you try asking again in a different way?" 