#!/usr/bin/env python3
"""
Enhanced Financial Question-Answering System with Hybrid Search & Reranking
Features:
- Hybrid search: Combines semantic (vector) + keyword (BM25) search
- Reranking: Uses FlashRank or Cohere for better result ordering
- Configurable search strategies
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    BM25_ENCODER_PKL,
    PINECONE_API_KEY,
    OPENAI_API_KEY,
    PINECONE_INDEX_NAME,
    validate_config
)

# Validate configuration
validate_config()

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.retrievers import PineconeHybridSearchRetriever
from pinecone_text.sparse import BM25Encoder
from langchain.schema import Document

class HybridFinancialQASystem:
    """
    Enhanced Question-Answering system with hybrid search and reranking
    - Combines semantic (dense) + keyword (sparse/BM25) search
    - Reranks results for better relevance
    """

    def __init__(self,
                 use_hybrid: bool = True,
                 use_reranking: bool = True,
                 reranker_type: str = "flashrank",  # "flashrank", "cohere", or "none"
                 index_name: str = None,
                 bm25_encoder_path: str = None):
        """
        Initialize the hybrid QA system

        Args:
            use_hybrid: Enable hybrid search (semantic + keyword)
            use_reranking: Enable reranking of results
            reranker_type: Type of reranker to use ("flashrank", "cohere", or "none")
            index_name: Pinecone index name (auto-selects based on use_hybrid)
            bm25_encoder_path: Path to saved BM25 encoder (for hybrid search)
        """
        # API keys
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        self.use_hybrid = use_hybrid
        self.use_reranking = use_reranking
        self.reranker_type = reranker_type

        # Auto-select index based on hybrid mode
        if index_name is None:
            index_name = "fintbx-hybrid-3072" if use_hybrid else "fintbx-semantic-3072"

        self.index_name = index_name

        print("🚀 INITIALIZING ENHANCED FINANCIAL QA SYSTEM")
        print("=" * 60)
        print(f"🔧 Configuration:")
        print(f"   • Hybrid Search: {'✅ Enabled' if use_hybrid else '❌ Disabled'}")
        print(f"   • Reranking: {'✅ Enabled (' + reranker_type + ')' if use_reranking else '❌ Disabled'}")
        print(f"   • Index: {index_name}")
        print("=" * 60)

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
                index_name=self.index_name,
                embedding=self.embeddings,
                pinecone_api_key=self.pinecone_api_key
            )
            print("✅ Pinecone vector store connected")
        except Exception as e:
            print(f"❌ Failed to connect to Pinecone: {e}")
            return

        # Initialize sparse encoder for hybrid search
        self.bm25_encoder = None
        if use_hybrid:
            try:
                # Try to load saved BM25 encoder
                if bm25_encoder_path is None:
                    bm25_encoder_path = "../Data/bm25_encoder.pkl"

                import pickle
                from pathlib import Path
                encoder_file = Path(bm25_encoder_path)

                if encoder_file.exists():
                    print(f"📂 Loading saved BM25 encoder from {encoder_file}...")
                    with open(encoder_file, 'rb') as f:
                        self.bm25_encoder = pickle.load(f)
                    print("✅ BM25 encoder loaded (fitted on corpus)")
                else:
                    print(f"⚠️ BM25 encoder not found at {encoder_file}")
                    print("   Run upload_to_pinecone_hybrid.py first to create it")
                    print("   Falling back to semantic-only search")
                    self.use_hybrid = False
            except Exception as e:
                print(f"⚠️ BM25 encoder initialization failed: {e}")
                print("   Falling back to semantic-only search")
                self.use_hybrid = False

        # Initialize reranker
        self.reranker = None
        if use_reranking:
            if reranker_type == "flashrank":
                try:
                    from flashrank import Ranker, RerankRequest
                    self.reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")
                    self.rerank_func = self._rerank_with_flashrank
                    print("✅ FlashRank reranker initialized")
                except ImportError:
                    print("⚠️ FlashRank not installed. Run: pip install flashrank")
                    print("   Disabling reranking")
                    self.use_reranking = False
                except Exception as e:
                    print(f"⚠️ FlashRank initialization failed: {e}")
                    self.use_reranking = False

            elif reranker_type == "cohere":
                try:
                    from langchain.retrievers.document_compressors import CohereRerank
                    # Note: Requires COHERE_API_KEY environment variable
                    self.reranker = CohereRerank(top_n=5)
                    self.rerank_func = self._rerank_with_cohere
                    print("✅ Cohere reranker initialized")
                except ImportError:
                    print("⚠️ Cohere not installed. Run: pip install cohere")
                    print("   Disabling reranking")
                    self.use_reranking = False
                except Exception as e:
                    print(f"⚠️ Cohere initialization failed: {e}")
                    self.use_reranking = False

        # Initialize ChatGPT
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=self.openai_api_key
            )
            print("✅ ChatGPT initialized")
        except Exception as e:
            print(f"❌ Failed to initialize ChatGPT: {e}")
            return

        # Create custom prompt
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a financial expert assistant helping users understand MATLAB Financial Toolbox documentation and financial concepts.

Context from Financial Toolbox documentation:
{context}

Question: {question}

Instructions:
1. Answer based ONLY on the provided context from the Financial Toolbox documentation
2. If the context contains MATLAB code or syntax examples, ALWAYS include them in your answer with proper formatting
3. Include function signatures, parameters, and usage examples exactly as they appear in the context
4. For mathematical formulas, explain the financial meaning
5. Be precise and cite specific page numbers when available
6. If the question cannot be answered from the context, say so clearly
7. Focus on practical financial applications with code examples

Format code examples using markdown code blocks:
```matlab
% Your MATLAB code here
```

Answer:"""
        )

        # Create retriever
        try:
            self.retriever = self._create_retriever()
            print("✅ Retriever created successfully")

            # Create QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever,
                chain_type_kwargs={"prompt": self.prompt_template},
                return_source_documents=True
            )
            print("✅ QA system ready!")
            self.ready = True
        except Exception as e:
            print(f"❌ Failed to create retriever/QA chain: {e}")
            import traceback
            traceback.print_exc()
            self.ready = False

    def _create_retriever(self):
        """Create the appropriate retriever based on configuration"""

        # Start with base retriever
        if self.use_hybrid:
            # Note: PineconeHybridSearchRetriever requires a Pinecone index
            # configured with dotproduct metric for sparse values
            # If your index doesn't support this, fall back to semantic search
            try:
                from pinecone import Pinecone

                pc = Pinecone(api_key=self.pinecone_api_key)
                index = pc.Index(self.index_name)  # Use the configured index name

                retriever = PineconeHybridSearchRetriever(
                    embeddings=self.embeddings,
                    sparse_encoder=self.bm25_encoder,
                    index=index,
                    top_k=10,  # Get more results for reranking
                    text_key="text"  # Field name for text content in metadata
                )
                print(f"   Using hybrid search retriever with index: {self.index_name}")
            except Exception as e:
                print(f"   ⚠️ Hybrid search not available: {e}")
                print("   Falling back to semantic search")
                retriever = self.vector_store.as_retriever(
                    search_kwargs={"k": 10}
                )
                self.use_hybrid = False
        else:
            # Standard semantic search
            retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 10}
            )
            print("   Using semantic search retriever")

        # Wrap with reranker if enabled
        if self.use_reranking and self.reranker:
            if self.reranker_type == "cohere":
                retriever = ContextualCompressionRetriever(
                    base_compressor=self.reranker,
                    base_retriever=retriever
                )
                print("   Wrapped with Cohere reranker")
            # FlashRank reranking is done manually in ask_question

        return retriever

    def _rerank_with_flashrank(self, query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
        """Rerank documents using FlashRank"""
        from flashrank import RerankRequest

        # Prepare passages for reranking
        passages = [{"text": doc.page_content} for doc in docs]

        # Rerank
        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.reranker.rerank(rerank_request)

        # Sort by score and get top_k
        reranked_docs = []
        for i, result in enumerate(results[:top_k]):
            # FlashRank returns results with 'id' attribute (index into original passages)
            idx = result.get('id', result.get('corpus_id', i))
            original_doc = docs[idx]
            # Optionally add score to metadata
            original_doc.metadata["rerank_score"] = result.get('score', 0.0)
            reranked_docs.append(original_doc)

        return reranked_docs

    def _rerank_with_cohere(self, query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
        """Rerank documents using Cohere (handled by ContextualCompressionRetriever)"""
        # This is handled automatically by the retriever wrapper
        return docs[:top_k]

    def ask_question(self, question: str, element_filter: dict = None):
        """Ask a question and get an answer with sources"""

        if not self.ready:
            return "❌ System not ready. Please check initialization."

        print(f"\n🤔 Question: {question}")
        print("-" * 60)

        try:
            # Custom retrieval with filter
            if element_filter:
                print(f"🔍 Applying filter: {element_filter}")
                relevant_docs = self.vector_store.similarity_search(
                    question,
                    k=10,  # Get more for reranking
                    filter=element_filter
                )

                if not relevant_docs:
                    return f"❌ No relevant documents found with filter {element_filter}"

                # Apply reranking if enabled
                if self.use_reranking and self.reranker_type == "flashrank":
                    print(f"🔄 Reranking {len(relevant_docs)} results...")
                    relevant_docs = self._rerank_with_flashrank(question, relevant_docs, top_k=5)
                else:
                    relevant_docs = relevant_docs[:5]

                # Create context
                context = "\n\n".join([doc.page_content for doc in relevant_docs])

                # Use LLM directly
                response = self.llm.invoke(
                    self.prompt_template.format(context=context, question=question)
                )
                answer = response.content
                source_docs = relevant_docs

            else:
                # Use the full QA chain
                if self.use_reranking and self.reranker_type == "flashrank":
                    # Manual reranking for FlashRank
                    initial_docs = self.retriever.get_relevant_documents(question)
                    print(f"🔄 Reranking {len(initial_docs)} results...")
                    reranked_docs = self._rerank_with_flashrank(question, initial_docs, top_k=5)

                    # Create context and answer
                    context = "\n\n".join([doc.page_content for doc in reranked_docs])
                    response = self.llm.invoke(
                        self.prompt_template.format(context=context, question=question)
                    )
                    answer = response.content
                    source_docs = reranked_docs
                else:
                    # Standard QA chain (includes Cohere reranking if configured)
                    result = self.qa_chain.invoke({"query": question})
                    answer = result["result"]
                    source_docs = result["source_documents"]

            print(f"💡 Answer:")
            print(answer)

            print(f"\n📚 Sources ({len(source_docs)} documents):")
            for i, doc in enumerate(source_docs, 1):
                element_type = doc.metadata.get('element_type', 'unknown')
                page = doc.metadata.get('page_number', 'N/A')
                section = doc.metadata.get('section', 'Unknown section')
                content_preview = doc.page_content[:100].replace('\n', ' ') + "..."

                # Show rerank score if available
                score_info = ""
                if 'rerank_score' in doc.metadata:
                    score_info = f" [score: {doc.metadata['rerank_score']:.3f}]"

                print(f"   {i}. [{element_type}] Page {page} - {section}{score_info}")
                print(f"      {content_preview}")

            return answer

        except Exception as e:
            error_msg = f"❌ Error processing question: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
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

        print("\n🎯 ENHANCED FINANCIAL QA SYSTEM - INTERACTIVE MODE")
        print("=" * 60)
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
                    try:
                        parts = user_input.split(':')
                        page_part = parts[0].strip()
                        query = parts[1].strip() if len(parts) > 1 else "financial"

                        page_range = page_part.split('pages')[1].strip()
                        start, end = map(int, page_range.split('-'))

                        self.search_page_range(query, start, end)
                    except:
                        print("❌ Invalid page range format. Use: 'pages 40-50: your query'")

                else:
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
    """Main function to start the enhanced QA system"""

    print("🎯 ENHANCED FINANCIAL TOOLBOX QA SYSTEM")
    print("With Hybrid Search & Reranking")
    print("=" * 60)

    # Initialize system with hybrid search and FlashRank reranking
    # Options:
    #   use_hybrid=True/False - Enable semantic + keyword search
    #   use_reranking=True/False - Enable reranking
    #   reranker_type="flashrank"/"cohere"/"none"
    #   index_name=None - Auto-selects based on use_hybrid
    #   bm25_encoder_path=None - Path to saved BM25 encoder

    # OPTION 1: Semantic search only (current index)
    # qa_system = HybridFinancialQASystem(
    #     use_hybrid=False,
    #     use_reranking=True,
    #     reranker_type="flashrank"
    # )

    # OPTION 2: Full hybrid search (requires hybrid index)
    # First run: upload_to_pinecone_hybrid.py
    bm25_path = str(BM25_ENCODER_PKL)
    index_name = PINECONE_INDEX_NAME

    qa_system = HybridFinancialQASystem(
        use_hybrid=True,
        use_reranking=True,
        reranker_type="flashrank",
        index_name=index_name,
        bm25_encoder_path=bm25_path
    )

    if not qa_system.ready:
        print("❌ Failed to initialize QA system")
        return

    print(f"\n🎉 System ready! You have access to:")
    print(f"   📊 2,124+ financial document chunks")
    print(f"   🔍 Hybrid search (semantic + keyword)")
    print(f"   🎯 Smart reranking for better results")
    print(f"   🤖 GPT-4 powered question answering")
    print(f"   📖 MATLAB Financial Toolbox expertise")

    # Show quick test
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
