import streamlit as st
from youtube_search import main as search_main
from youtube_downloader import main as downloader_main
import hmac
import time

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["username"], st.secrets.credentials.username):
            if hmac.compare_digest(st.session_state["password"], st.secrets.credentials.password):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store the password.
                del st.session_state["username"]  # Don't store the username.
            else:
                st.session_state["password_correct"] = False
        else:
            st.session_state["password_correct"] = False

    # First run or user logged out
    if "password_correct" not in st.session_state:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Log in", on_click=password_entered)
        return False

    # Password correct
    elif st.session_state["password_correct"]:
        return True

    # Password incorrect
    return False

def main():
    st.set_page_config(
        page_title="YouTube Tools",
        page_icon="🎥",
        layout="wide"
    )

    if not check_password():
        st.error("Please log in to access the application.")
        # Add a delay to prevent brute force attacks
        time.sleep(0.5)
        return

    # Show logout button in sidebar
    if st.sidebar.button("Logout"):
        del st.session_state["password_correct"]
        st.experimental_rerun()
    
    st.title("YouTube Tools 🎥")
    st.markdown("---")

    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["YouTube Search", "YouTube Downloader"])

    with tab1:
        search_main()

    with tab2:
        downloader_main()

    # Add footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>Made with ❤️ using Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 