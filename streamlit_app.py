"""
📚 Book Finder - Simple Search
Streamlit app for book search (lightweight version)
"""

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# Semantic search is optional
SEARCH_AVAILABLE = False
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from search.semantic_search import SemanticSearchEngine
    SEARCH_AVAILABLE = True
except:
    pass  # Fall back to keyword search

# Page config
st.set_page_config(
    page_title="Book Finder",
    page_icon="📚",
    layout="wide"
)

# Database path
DB_PATH = "data/books.db"

@st.cache_resource
def load_search_engine():
    """Load the search engine (cached)."""
    if not SEARCH_AVAILABLE:
        return None
    try:
        engine = SemanticSearchEngine()
        return engine
    except Exception as e:
        st.error(f"Failed to load search engine: {e}")
        return None

@st.cache_data
def get_database_stats():
    """Get database statistics."""
    if not Path(DB_PATH).exists():
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM books")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM books WHERE description IS NOT NULL")
        with_desc = cursor.fetchone()[0]
        
        conn.close()
        
        return {'total': total, 'with_descriptions': with_desc}
    except:
        return None

def get_recent_books(limit=20):
    """Fetch recent books from database."""
    if not Path(DB_PATH).exists():
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT isbn, title, description, authors, genres, publish_date
            FROM books
            ORDER BY created_at DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def search_books_semantic(query, top_k=10):
    """Semantic search for books."""
    engine = load_search_engine()
    if engine is None:
        st.error("Search engine not available")
        return []
    
    try:
        results = engine.search(query=query, top_k=top_k)
        return results
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

def search_books_simple(query, limit=20):
    """Simple keyword search in database."""
    if not Path(DB_PATH).exists():
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        sql_query = """
            SELECT isbn, title, description, authors, genres, publish_date
            FROM books
            WHERE title LIKE ? OR description LIKE ? OR authors LIKE ? OR genres LIKE ?
            ORDER BY 
                CASE 
                    WHEN title LIKE ? THEN 1
                    WHEN authors LIKE ? THEN 2
                    WHEN description LIKE ? THEN 3
                    ELSE 4
                END,
                created_at DESC
            LIMIT ?
        """
        pattern = f"%{query}%"
        df = pd.read_sql_query(
            sql_query, 
            conn, 
            params=(pattern, pattern, pattern, pattern, pattern, pattern, pattern, limit)
        )
        conn.close()
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Search error: {e}")
        return []

def get_random_books(limit=20):
    """Get random books for discovery."""
    if not Path(DB_PATH).exists():
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        sql = """
            SELECT isbn, title, description, authors, genres, publish_date
            FROM books
            WHERE description IS NOT NULL
            ORDER BY RANDOM()
            LIMIT ?
        """
        df = pd.read_sql_query(sql, conn, params=(limit,))
        conn.close()
        return df.to_dict('records')
    except:
        return []

def display_book(book, show_score=False):
    """Display a single book card."""
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(book.get('title', 'Unknown Title'))
        
        with col2:
            if show_score and 'similarity_score' in book:
                score = book['similarity_score']
                st.metric("Match", f"{score*100:.1f}%")
        
        # Metadata
        meta_parts = []
        if book.get('authors'):
            meta_parts.append(f"**Authors:** {book['authors']}")
        if book.get('genres'):
            meta_parts.append(f"**Genres:** {book['genres']}")
        if book.get('publish_date'):
            meta_parts.append(f"**Published:** {book['publish_date']}")
        
        if meta_parts:
            st.markdown(" • ".join(meta_parts))
        
        # Description
        if book.get('description'):
            desc = book['description']
            if len(desc) > 300:
                desc = desc[:300] + "..."
            st.write(desc)
        
        # ISBN
        st.caption(f"ISBN: {book.get('isbn', 'N/A')}")
        
        st.divider()

# Main app
def main():
    st.title("📚 Book Finder")
    st.markdown("*Intelligent book search and recommendations*")
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.info(
            "This app helps you find books using natural language descriptions. "
            "Just describe what you're looking for!"
        )
        
        # Database stats
        stats = get_database_stats()
        if stats:
            st.metric("Total Books", f"{stats['total']:,}")
            st.metric("With Descriptions", f"{stats['with_descriptions']:,}")
        
        st.divider()
        
        # Search settings
        st.subheader("⚙️ Settings")
        search_mode = st.radio(
            "Search Mode",
            ["Semantic Search", "Keyword Search"],
            help="Semantic understands meaning, Keyword finds exact matches"
        )
        
        num_results = st.slider(
            "Number of Results",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🔍 Search", "🎲 Discover", "ℹ️ Help"])
    
    with tab1:
        st.header("Search for Books")
        
        # Search box
        query = st.text_input(
            "What are you looking for?",
            placeholder="e.g., A mystery novel set in Victorian London, or books about machine learning",
            help="Describe the book you want in natural language"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_button = st.button("🔍 Search", type="primary", use_container_width=True)
        
        # Perform search
        if search_button and query:
            with st.spinner("Searching..."):
                if search_mode == "Semantic Search" and SEARCH_AVAILABLE:
                    results = search_books_semantic(query, top_k=num_results)
                else:
                    results = search_books_simple(query, limit=num_results)
            
            if results:
                st.success(f"Found {len(results)} results")
                st.divider()
                
                for book in results:
                    display_book(book, show_score=search_mode == "Semantic Search")
            else:
                st.warning("No results found. Try a different query.")
        
        elif search_button:
            st.warning("Please enter a search query")
    
    with tab2:
        st.header("Discover Random Books")
        st.markdown("Not sure what to look for? Explore our collection!")
        
        if st.button("🎲 Show Random Books", use_container_width=True):
            with st.spinner("Loading..."):
                books = get_random_books(limit=num_results)
            
            if books:
                st.success(f"Showing {len(books)} random books")
                st.divider()
                
                for book in books:
                    display_book(book)
            else:
                st.warning("No books found in database")
    
    with tab3:
        st.header("How to Use")
        
        st.markdown("""
        ### 🔍 Search Modes
        
        **Semantic Search** (Recommended)
        - Understands the meaning of your query
        - Use natural language descriptions
        - Example: *"A thrilling mystery with a strong female detective"*
        
        **Keyword Search**
        - Finds exact word matches
        - Faster but less intelligent
        - Example: *"detective mystery"*
        
        ### 💡 Tips
        
        1. **Be descriptive**: The more details, the better the results
        2. **Use natural language**: Write like you're talking to a friend
        3. **Include genres**: Fiction, non-fiction, mystery, sci-fi, etc.
        4. **Mention topics**: Machine learning, history, cooking, etc.
        
        ### 📊 About the Data
        
        This database contains thousands of books with:
        - Titles and authors
        - Detailed descriptions
        - Genre classifications
        - Publication dates
        
        Data is sourced from library catalogs and enriched with OpenLibrary and OpenAlex.
        """)
        
        st.divider()
        
        st.subheader("🚀 Deployment")
        st.markdown("""
        This app is deployed using Streamlit Cloud.
        
        To deploy your own:
        1. Push code to GitHub
        2. Go to [share.streamlit.io](https://share.streamlit.io)
        3. Connect your repo
        4. Deploy!
        """)

if __name__ == "__main__":
    main()