import pathlib
import sys; sys.path.append(str(pathlib.Path(__file__).parent.parent))
import streamlit as st


def load_home_page():
    st.set_page_config(
        page_title="Tiger QE AI Solutions",
        page_icon="🤖",
    )

    st.write("# Welcome to the Tiger QE AI Solutions! 🚀 Your Gateway to Smarter Testing!")
    st.sidebar.success("Select an option page above")

    st.markdown(f"""
        <table style="margin-left: auto; margin-right: auto; border-collapse: collapse; border: none;">
            <tr><th style="text-align: center;"> Testing Reinvented: AI at Every Phase! </th></tr>
            <tr><td>Functional Test Case Generator</td></tr>
            <tr><td>End to End Test Case Generator</td></tr>
            <tr><td>Xpath Generator</td></tr>
            <tr><td>SQL Query Generator</td></tr>
            <tr><td>LLM Prompt Generator</td></tr>
        </table>
    """, unsafe_allow_html=True)

    st.markdown("""
        **👈 Select a page from the sidebar** to see some examples
        of what our Accelerator can do!
        """)

    st.divider()

    st.markdown("""    
        ### Contact Us
        - Reach us at [QE Core Team](mailto:QE@tigeranalytics.com)


        ### Want to learn more?
        - Check out [streamlit.io](https://streamlit.io)

    """)





if __name__ == "__main__":
    load_home_page()

