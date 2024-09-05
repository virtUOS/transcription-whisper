import streamlit as st

from streamlit_quill import st_quill

st.markdown("""
<style>
.stElementContainer:has(> iframe) {
  height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
""", unsafe_allow_html=True)

# Spawn a new Quill editor
content = st_quill(key='foobar')

# Display editor's content as you type
content