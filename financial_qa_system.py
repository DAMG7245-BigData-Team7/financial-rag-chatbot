#!/usr/bin/env python3
"""
Financial Question-Answering System
Interactive RAG system using your Lab 1 AURELIA + Pinecone corpus
"""

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import sys

class FinancialQASystem:
    """
    Interactive Question-Answering system for financial documents
    Built on your Lab 1 AURELIA + Pinecone corpus
    """

    def __init__(self):
        # API keys
        self.pinecone_api_key = "pcsk_6sow6P_3XHg3HPsuGRcxHGZUSEB1VcM4D4Eedo4kQGvBMXiSUL5fhWAF4rNtnEL1m7cPtv"
        self.openai_api_key = "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"

        print("🚀 INITIALIZING FINANCIAL QA SYSTEM")
        print("=" * 50)

        # Initialize embeddings
        try:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-large",
                api_key=self.openai_api_key
            )
            print("✅ OpenAI embeddings initialized")
        except Exception as e:
            print(f"❌ Failed to initialize embeddings: {e}")
            return

        # Initialize vector store
        try:
            self.vector_store = PineconeVectorStore(
                index_name="fintbx-3072-lab1",
                embedding=self.embeddings,
                pinecone_api_key=self.pinecone_api_key
            )
            print("✅ Pinecone vector store connected")
        except Exception as e:
            print(f"❌ Failed to connect to Pinecone: {e}")
            return

        # Initialize ChatGPT
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",  # Fast and cost-effective
                temperature=0.1,  # Low temperature for factual responses
                api_key=self.openai_api_key
            )
            print("✅ ChatGPT initialized")
        except Exception as e:
            print(f"❌ Failed to initialize ChatGPT: {e}")
            return

        # Create custom prompt for financial QA
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a financial expert assistant helping users understand MATLAB Financial Toolbox documentation and financial concepts.

Context from Financial Toolbox documentation:
{context}

Question: {question}

Instructions:
1. Answer based ONLY on the provided context from the Financial Toolbox documentation
2. If the context contains MATLAB code, explain what it does and how to use it
3. For mathematical formulas, explain the financial meaning
4. Be precise and cite specific page numbers when available
5. If the question cannot be answered from the context, say so clearly
6. Focus on practical financial applications

Answer:"""
        )

        # Create the QA chain
        try:
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vector_store.as_retriever(
                    search_kwargs={"k": 5}  # Retrieve top 5 relevant chunks
                ),
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True
            )
            print("✅ QA system ready!")
            self.ready = True
        except Exception as e:
            print(f"❌ Failed to create QA chain: {e}")
            self.ready = False

    def ask_question(self, question: str, element_filter: dict = None):
        """Ask a question and get an answer with sources"""

        if not self.ready:
            return "❌ System not ready. Please check initialization."

        print(f"\n🤔 Question: {question}")
        print("-" * 60)

        try:
            # Custom retrieval if filter specified
            if element_filter:
                print(f"🔍 Applying filter: {element_filter}")
                relevant_docs = self.vector_store.similarity_search(
                    question,
                    k=5,
                    filter=element_filter
                )

                if not relevant_docs:
                    return f"❌ No relevant documents found with filter {element_filter}"

                # Create context from filtered docs
                context = "\n\n".join([doc.page_content for doc in relevant_docs])

                # Use LLM directly with custom context
                response = self.llm.invoke(
                    self.prompt_template.format(context=context, question=question)
                )
                answer = response.content
                source_docs = relevant_docs

            else:
                # Use the full QA chain
                result = self.qa_chain.invoke({"query": question})
                answer = result["result"]
                source_docs = result["source_documents"]

            print(f"💡 Answer:")
            print(answer)

            print(f"\n📚 Sources:")
            for i, doc in enumerate(source_docs, 1):
                element_type = doc.metadata.get('element_type', 'unknown')
                page = doc.metadata.get('page_number', 'N/A')
                section = doc.metadata.get('section', 'Unknown section')
                content_preview = doc.page_content[:100].replace('\n', ' ') + "..."

                print(f"   {i}. [{element_type}] Page {page} - {section}")
                print(f"      {content_preview}")

            return answer

        except Exception as e:
            error_msg = f"❌ Error processing question: {e}"
            print(error_msg)
            return error_msg

    def suggest_questions(self):
        """Suggest sample questions to get started"""

        suggestions = [
            # Basic financial concepts
            "What is the Black-Scholes model and how is it used?",
            "How do I calculate the internal rate of return in MATLAB?",
            "What are the main portfolio optimization functions available?",

            # MATLAB specific
            "Show me examples of the blsprice function",
            "How do I use the irr function for cash flow analysis?",
            "What Monte Carlo simulation functions are available?",

            # Advanced topics
            "How do I implement CVaR portfolio optimization?",
            "What are the different yield calculation methods?",
            "How do I model interest rate derivatives?",

            # Code examples
            "Show me MATLAB code for option pricing",
            "Give me an example of portfolio risk calculation",
            "How do I create a yield curve in MATLAB?"
        ]

        print("\n💡 SUGGESTED QUESTIONS:")
        print("=" * 30)

        for i, question in enumerate(suggestions, 1):
            print(f"{i:2d}. {question}")

    def search_by_type(self, query: str, element_type: str):
        """Search for specific element types"""

        type_filters = {
            "code": {"element_type": "code_block"},
            "tables": {"element_type": "table_block"},
            "text": {"element_type": "text"},
            "matlab": {"element_type": "code_block", "language": "matlab"},
            "matlab_financial": {"element_type": "code_block", "language": "matlab_financial"}
        }

        if element_type not in type_filters:
            print(f"❌ Unknown element type. Available: {list(type_filters.keys())}")
            return

        return self.ask_question(query, type_filters[element_type])

    def search_page_range(self, query: str, start_page: int, end_page: int):
        """Search within specific page range"""

        page_filter = {
            "page_number": {"$gte": start_page, "$lte": end_page}
        }

        return self.ask_question(query, page_filter)

    def interactive_mode(self):
        """Start interactive question-answering session"""

        if not self.ready:
            print("❌ System not ready. Cannot start interactive mode.")
            return

        print("\n🎯 FINANCIAL QA SYSTEM - INTERACTIVE MODE")
        print("=" * 50)
        print("💡 Ask questions about the Financial Toolbox documentation")
        print("📝 Type 'help' for commands, 'quit' to exit")
        print("🔍 Examples: 'code: option pricing' or 'pages 40-50: yield curves'")

        while True:
            try:
                user_input = input("\n❓ Your question: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                elif user_input.lower() in ['help', 'h']:
                    self.show_help()

                elif user_input.lower() in ['suggestions', 'examples']:
                    self.suggest_questions()

                elif user_input.startswith('code:'):
                    query = user_input[5:].strip()
                    self.search_by_type(query, "code")

                elif user_input.startswith('matlab:'):
                    query = user_input[7:].strip()
                    self.search_by_type(query, "matlab")

                elif user_input.startswith('tables:'):
                    query = user_input[7:].strip()
                    self.search_by_type(query, "tables")

                elif 'pages' in user_input.lower() and '-' in user_input:
                    # Parse "pages 40-50: query"
                    try:
                        parts = user_input.split(':')
                        page_part = parts[0].strip()
                        query = parts[1].strip() if len(parts) > 1 else "financial"

                        # Extract page numbers
                        page_range = page_part.split('pages')[1].strip()
                        start, end = map(int, page_range.split('-'))

                        self.search_page_range(query, start, end)
                    except:
                        print("❌ Invalid page range format. Use: 'pages 40-50: your query'")

                else:
                    # Regular question
                    self.ask_question(user_input)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def show_help(self):
        """Show available commands"""

        print("\n📖 AVAILABLE COMMANDS:")
        print("-" * 25)
        print("• Regular question: 'What is the Black-Scholes model?'")
        print("• Code search: 'code: option pricing'")
        print("• MATLAB search: 'matlab: portfolio optimization'")
        print("• Table search: 'tables: interest rates'")
        print("• Page range: 'pages 40-50: yield curves'")
        print("• Get suggestions: 'suggestions' or 'examples'")
        print("• Help: 'help'")
        print("• Quit: 'quit' or 'exit'")

def main():
    """Main function to start the QA system"""

    print("🎯 FINANCIAL TOOLBOX QA SYSTEM")
    print("Built on your Lab 1 AURELIA + Pinecone corpus")
    print("=" * 60)

    # Initialize system
    qa_system = FinancialQASystem()

    if not qa_system.ready:
        print("❌ Failed to initialize QA system")
        return

    print(f"\n🎉 System ready! You have access to:")
    print(f"   📊 2,124+ financial document chunks")
    print(f"   🔍 Structure-aware search (code, tables, text)")
    print(f"   🤖 GPT-4 powered question answering")
    print(f"   📖 MATLAB Financial Toolbox expertise")

    # Show some quick examples
    print(f"\n⚡ QUICK TEST:")
    qa_system.ask_question("What is the blsprice function used for?")

    # Start interactive mode
    response = input("\n🚀 Start interactive mode? (y/n): ").lower()
    if response in ['y', 'yes']:
        qa_system.interactive_mode()
    else:
        print("💡 Run this script again and choose 'y' to start asking questions!")
        qa_system.suggest_questions()

if __name__ == "__main__":
    main()