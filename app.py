#  app.py
import streamlit as st

st.set_page_config(
    page_title="TOS Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("TOS Streamlit Dashboard")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Select a page",
    ("Default", "Page2"),
    format_func=lambda x: "Live GEX Dashboard with all charts" if x == "Default" else "Alternative dashboard view with 5 specialized charts"
)

st.info("👈 Use the sidebar to navigate between pages")

if page == "Default":
    st.write("Welcome to the TOS Dashboard. This is the Live GEX Dashboard with all charts.")
    # Add content for Default page here
elif page == "Page2":
    st.write("Welcome to the Alternative dashboard view with 5 specialized charts.")
    # Add content for Page2 here
