"""
Script to update the LlamaIndex RAG system with the latest document content.
This will rebuild the index to ensure all content is properly searchable.
"""

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    Document
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
import config
import os
from pathlib import Path
import shutil


print("running update_llama_index file")
print("🔄 Updating RAG system with fresh document content...")

# Configure debug handler for visibility into index construction
llama_debug = LlamaDebugHandler(print_trace_on_end=True)
callback_manager = CallbackManager([llama_debug])

# Configure global settings with embeddings and LLM
print("🔄 Initializing embedding model and LLM...")
llm = Gemini(api_key=config.GOOGLE_API_KEY, model_name="gemini-2.5-flash")
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Configure settings
Settings.llm = llm
Settings.embed_model = embed_model
Settings.callback_manager = callback_manager

# Path settings
INDEX_STORAGE_PATH = "./index_storage"
PDF_DIR = "./pdf"

def load_documents():
    """Load all documents from the PDF directory"""
    documents = []
    
    # First try to load text files for better parsing
    if os.path.exists(PDF_DIR):
        txt_files = list(Path(PDF_DIR).glob("*.txt"))
        if txt_files:
            print(f"📚 Loading {len(txt_files)} text files from {PDF_DIR}...")
            reader = SimpleDirectoryReader(input_dir=PDF_DIR, required_exts=[".txt"])
            documents.extend(reader.load_data())
    
    # Also load PDFs
    if os.path.exists(PDF_DIR):
        pdf_files = list(Path(PDF_DIR).glob("*.pdf"))
        if pdf_files:
            print(f"📚 Loading {len(pdf_files)} PDF files from {PDF_DIR}...")
            # Only load PDFs if their text version doesn't exist
            for pdf_file in pdf_files:
                txt_file = pdf_file.with_suffix('.txt')
                if not txt_file.exists():
                    reader = SimpleDirectoryReader(input_files=[str(pdf_file)])
                    pdf_docs = reader.load_data()
                    documents.extend(pdf_docs)
                    print(f"✓ Loaded PDF: {pdf_file}")
    
    if not documents:
        print("❌ No documents found in the PDF directory.")
        return None
    
    print(f"✓ Successfully loaded {len(documents)} documents")
    return documents

def process_documents(documents):
    """Process documents into nodes with sentence splitting for more effective chunking"""
    print("🔄 Processing documents with sentence splitting...")
    
    # Use sentence splitter for more granular and focused chunks
    sentence_splitter = SentenceSplitter(
        chunk_size=256,
        chunk_overlap=25
    )
    
    nodes = sentence_splitter.get_nodes_from_documents(documents)
    print(f"✓ Processed {len(nodes)} nodes from {len(documents)} documents")
    return nodes

def build_index(nodes):
    """Build a new index from the processed nodes"""
    print("🔄 Building new vector index...")
    
    # Create storage context to save index
    storage_context = StorageContext.from_defaults()
    
    # Create vector index
    index = VectorStoreIndex(nodes, storage_context=storage_context)
    
    # Save index
    print(f"🔄 Saving index to {INDEX_STORAGE_PATH}...")
    index.storage_context.persist(persist_dir=INDEX_STORAGE_PATH)
    print(f"✓ Index built and saved successfully")
    
    return index

def main():
    """Main function to update the RAG system"""
    print("\n===== 🔄 RAG System Update =====\n")
    
    if os.path.exists(INDEX_STORAGE_PATH):
        print(f"🗑️ Clearing old index at {INDEX_STORAGE_PATH}...")
        try:
            for f in os.listdir(INDEX_STORAGE_PATH):
                fp = os.path.join(INDEX_STORAGE_PATH, f)
                if os.path.isfile(fp):
                    os.remove(fp)
            print("✓ Old index cleared successfully.")
        except OSError as e:
            print(f"⚠️ Could not clear, continuing anyway...")
            
    # Load documents
    documents = load_documents()
    if not documents:
        print("❌ Failed to load documents. Exiting.")
        return
    
    # Process documents into nodes
    nodes = process_documents(documents)
    
    # Build and save the index
    index = build_index(nodes)
    
    print("\n✅ RAG system updated successfully!")
    print(f"✅ {len(nodes)} nodes indexed from {len(documents)} documents")
    print("\nYou can now run simple_rag.py to query the updated system.")

if __name__ == "__main__":
    main()