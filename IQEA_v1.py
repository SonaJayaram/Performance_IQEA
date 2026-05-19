import streamlit as st

st.set_page_config(page_title="IQEA Platform", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f4f6f9;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #C2410C, #7C2D12);
    padding-top: 20px;
}
[data-testid="stSidebar"] * { color: white !important; }

.card {
    background-color: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
    margin-bottom: 20px;
}
.section-title { font-size: 20px; font-weight: 600; margin-bottom: 10px; }
.block-container { padding: 2rem 3rem; }
</style>
""", unsafe_allow_html=True)

st.sidebar.image(r"C:\Users\sathanantham.aru\Downloads\IQEA.ai.png", width=150)
st.sidebar.markdown("### 🚀 Automation Suite")

page = st.sidebar.radio(
    "Go to",
    ["🏠 Home", "🧠 IQEA", "🔁 Self Healing", "🔗 API"],
    index=0
)

# PAGE ROUTING
if page == "🏠 Home":
    st.title("🤖 TigerQE AI Platform - iQEA")
    st.markdown("""
    <div class="card">
        <div class="section-title">🚀 IQEA - End to End Automation Platform</div>
        <ul>
            <li>Low-code / No-code E2E test artefacts generation</li>
            <li>AI-augmented test case & automation code generation</li>
            <li>Data-driven decisions (~30% efficiency gain)</li>
            <li>AI-powered self-healing for UI changes</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="card">
            <div class="section-title">🔁 Web Self Healing</div>
            <p>Maintain large regression suites efficiently using AI-driven healing.</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card">
            <div class="section-title">🔗 API Automation</div>
            <p>Seamless API testing with integrated performance testing.</p>
        </div>""", unsafe_allow_html=True)

elif page == "🧠 IQEA":
    st.markdown('<div class="card">Self Healing automation UI will be integrated here.</div>', unsafe_allow_html=True)
    import pages.Iqea

elif page == "🔁 Self Healing":
    st.markdown('<div class="card">Self Healing automation UI will be integrated here.</div>', unsafe_allow_html=True)
    import pages.selfhealing
elif page == "🔗 API":
    st.markdown('<div class="card">Self Healing automation UI will be integrated here.</div>', unsafe_allow_html=True)
    import pages.api