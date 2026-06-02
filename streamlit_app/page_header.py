import streamlit as st


def render_page_header() -> None:
    """Render the application header."""
    col1, col2 = st.columns([1, 8])
    with col1:
        logo = (
            "https://upload.wikimedia.org/wikipedia/commons/5/51/"
            "IBM_logo.svg"
        )
        st.image(logo, width=80)
    with col2:
        st.title("RVTools to IBM Cloud VPC")
