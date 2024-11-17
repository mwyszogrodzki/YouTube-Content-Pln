import streamlit as st
import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import tempfile
import os

def check_auth():
    """Check if user is authenticated"""
    if "password_correct" not in st.session_state:
        st.error("Please log in first")
        st.stop()
    if not st.session_state["password_correct"]:
        st.error("Please log in first")
        st.stop()

def visualize_knowledge_graph(relationships):
    """Create an interactive network graph"""
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
    
    # Add nodes and edges
    for rel in relationships:
        entity = rel['entity']
        attribute = rel['attribute']
        relationship = rel['relationship']
        
        # Add nodes
        net.add_node(entity, label=entity, title=entity, color="#00ff1e")
        net.add_node(attribute, label=attribute, title=attribute, color="#ff9999")
        
        # Add edge
        net.add_edge(entity, attribute, label=relationship, title=rel['description'])
    
    # Generate the HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
        net.save_graph(tmp_file.name)
        return tmp_file.name

def create_markdown_doc(keywords, relationships, headings):
    """Create a markdown document from the knowledge base"""
    md_content = "# Knowledge Base\n\n"
    
    # Add keywords section
    md_content += "## Keywords\n"
    md_content += ", ".join(keywords.split(", ")) + "\n\n"
    
    # Add relationships section
    md_content += "## Relationships\n\n"
    for rel in relationships:
        md_content += f"### {rel['entity']}\n"
        md_content += f"- {rel['relationship']} {rel['attribute']}\n"
        md_content += f"- Description: {rel['description']}\n\n"
    
    # Add headings section
    md_content += "## Document Structure\n\n"
    for heading in headings:
        prefix = "#" * (int(heading['heading'][1]) + 1)
        md_content += f"{prefix} {heading['value']}\n"
    
    return md_content

def main():
    check_auth()
    
    st.title("Knowledge Base Viewer")
    
    # Get knowledge base from session state or show file uploader
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = None
    
    # File uploader for JSON
    uploaded_file = st.file_uploader("Upload Knowledge Base JSON", type=['json'])
    if uploaded_file:
        try:
            content = json.load(uploaded_file)
            if isinstance(content, list) and len(content) == 3:
                st.session_state.knowledge_base = {
                    'keywords': content[0],
                    'relationships': content[1],
                    'headings': content[2]
                }
            else:
                st.error("Invalid JSON format")
        except Exception as e:
            st.error(f"Error loading JSON: {str(e)}")
    
    # Display knowledge base if available
    if st.session_state.knowledge_base:
        kb = st.session_state.knowledge_base
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "Overview", 
            "Knowledge Graph", 
            "Relationships Table", 
            "Document Structure"
        ])
        
        with tab1:
            st.header("Keywords")
            st.write(kb['keywords'])
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                # Download JSON
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(kb, indent=2),
                    file_name="knowledge_base.json",
                    mime="application/json"
                )
            
            with col2:
                # Download Markdown
                md_content = create_markdown_doc(
                    kb['keywords'],
                    kb['relationships'],
                    kb['headings']
                )
                st.download_button(
                    label="Download Markdown",
                    data=md_content,
                    file_name="knowledge_base.md",
                    mime="text/markdown"
                )
        
        with tab2:
            st.header("Knowledge Graph")
            graph_file = visualize_knowledge_graph(kb['relationships'])
            with open(graph_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=800)
            os.unlink(graph_file)
        
        with tab3:
            st.header("Relationships")
            df = pd.DataFrame(kb['relationships'])
            st.dataframe(
                df,
                column_config={
                    "entity": "Entity",
                    "relationship": "Relationship",
                    "attribute": "Attribute",
                    "description": "Description"
                },
                hide_index=True
            )
        
        with tab4:
            st.header("Document Structure")
            for heading in kb['headings']:
                level = int(heading['heading'][1])
                st.markdown(f"{'#' * level} {heading['value']}")

if __name__ == "__main__":
    main() 