import streamlit as st
import requests

st.set_page_config(page_title="AI SDLC Workflow", layout="wide")

# ---------- UI Elements ----------

st.title("💻 AI-Powered SDLC Workflow")

requirements = st.text_area("📌 Enter your project requirements", height=150)

if st.button("🚀 Run Workflow"):
    with st.spinner("Running the AI workflow..."):
        try:
            # Call your FastAPI backend endpoint
            response = requests.post(
                "http://localhost:8000/run",  # replace with your actual endpoint
                json={"requirements": requirements}
            )

            data = response.json()

            st.subheader("🧾 SDLC Output")

            if "user_stories" in data:
                st.markdown("### 📝 User Stories")
                st.markdown(data["user_stories"])

            if "design_documents" in data:
                st.markdown("### 🏗️ Design Document")
                st.markdown(data["design_documents"])

            if "generated_code" in data:
                st.markdown("### 💻 Generated Code")
                for role, code_block in data["generated_code"].items():
                    st.code(code_block, language="python")

            if "test_cases" in data:
                st.markdown("### 🧪 Test Cases")
                st.code(data["test_cases"], language="python")

            if "qa_test_result" in data:
                st.markdown("### ✅ QA Result")
                st.success(data["qa_test_result"])

            st.markdown("---")
            st.success("🎉 Workflow Complete")

        except Exception as e:
            st.error(f"Something went wrong: {e}")
