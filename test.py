import streamlit as st
from streamlit_quill import st_quill

# Add a header for easy viewing
st.header("Quill Editor with Limited Height")

# Custom CSS for limiting the iframe height and adding a border for visualization
st.markdown("""
<style>
.element-container:has(> iframe) {
  height: 300px;
  overflow-y: scroll;
  overflow-x: hidden;
}
</style>
""", unsafe_allow_html=True)

# Spawn a new Quill editor
content = st_quill(key='editor')

# Display editor's content as you type
st.write(content)