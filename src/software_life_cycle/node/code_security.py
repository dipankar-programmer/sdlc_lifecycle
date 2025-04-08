from langchain_core.messages import HumanMessage, SystemMessage
from software_life_cycle.state.state import SoftwareLifecycle
from software_life_cycle.LLM.llm import llm
import json
from software_life_cycle.utils.batching import chunk_generated_code
from typing import Literal

# def chunk_generated_code(data, token_limit: int = 5500) -> list:
#     """
#     Splits a dictionary or string into chunks based on token limits.
#     - For `dict`, splits by key-value.
#     - For `str`, splits by lines.
#     """
#     estimated_tokens = lambda text: len(str(text)) // 4
#     batches = []

#     if isinstance(data, dict):
#         current_batch = {}
#         current_tokens = 0

#         for key, value in data.items():
#             tokens = estimated_tokens(value)
#             if current_tokens + tokens > token_limit:
#                 if current_batch:
#                     batches.append(current_batch)
#                     current_batch = {}
#                     current_tokens = 0
#             current_batch[key] = value
#             current_tokens += tokens

#         if current_batch:
#             batches.append(current_batch)

#     elif isinstance(data, str):
#         lines = data.splitlines()
#         current_batch = []
#         current_tokens = 0

#         for line in lines:
#             tokens = estimated_tokens(line)
#             if current_tokens + tokens > token_limit:
#                 batches.append("\n".join(current_batch))
#                 current_batch = []
#                 current_tokens = 0
#             current_batch.append(line)
#             current_tokens += tokens

#         if current_batch:
#             batches.append("\n".join(current_batch))

#     return batches


#step 8: security review code
def code_security_review(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """LLM analyzes the generated code for security vulnerabilities."""
    print("*" * 50 + f" AI SECURITY REVIEW (Attempt {state.code_security_attempt + 1}/3) " + "*" * 50)

    if not state.generated_code:
        print("No generated code available for security review.")
        return state

    code_chunks = chunk_generated_code(state.generated_code, token_limit=5500)
    batch_responses = []

    for idx, chunk in enumerate(code_chunks):
        chunk_str = json.dumps(chunk, indent=2) if isinstance(chunk, dict) else chunk
        prompt_content = f"Here is the generated code (Chunk {idx+1}):\n{chunk_str}\n\n"

        if state.feedback.strip():
            prompt_content += (
                f"### Previous Feedback:\n{state.feedback.strip()}\n"
                f"### Ensure any identified vulnerabilities are mitigated.\n"
            )

        prompt_content += """
        **Security Checks:**
        SQL Injection  
        XSS (Cross-site scripting)  
        Hardcoded Secrets  
        Weak Authentication

        **Response Format:**
        - Decision: ('secure' or 'fix')
        - Feedback: Bullet points explaining security risks and fixes.
          make sure to keep the feedback extremely concise and clear
        """

        messages = [
            SystemMessage(content="You are a cybersecurity expert. Analyze the given code for security vulnerabilities."),
            HumanMessage(content=prompt_content)
        ]

        try:
            response = llm.invoke(messages).content.strip()
            print(f"Security review response for chunk {idx+1}")
            batch_responses.append(f"[Chunk {idx+1}]: {response}")
        except Exception as e:
            print(f"Error in LLM security review for chunk {idx+1}: {e}")
            batch_responses.append(f"[Chunk {idx+1}]: ERROR during security review")

    full_response = "\n\n".join(batch_responses)
    print(f"🔐 Combined Security Review Response:\n{full_response}")

    updated_feedback = state.feedback + f"\n[Security Review]: {full_response}"
    decision = "secure" if "secure" in full_response.lower() else "fix"

    return state.model_copy(update={
        "security_feedback": decision,
        "feedback": updated_feedback,
        "code_security_attempt": state.code_security_attempt + 1
    })


def security_route(state: SoftwareLifecycle) -> Literal["generate_test_cases", "orchestrate_code_generation"]:
    """LLM decision determines if the code is secure or needs improvements."""
    print("*" * 50 + " AI SECURITY REVIEW DECISION " + "*" * 50)

    security_decision = state.security_feedback.strip().lower()

    if state.code_security_attempt >= 2 or "secure" in security_decision:
        print(" Security Approved! Saving final code...")

        # Convert dict to readable string
        if isinstance(state.generated_code, dict):
            final_code = ""
            for role, code in state.generated_code.items():
                if isinstance(code, str):
                    final_code += f"# {role.upper()}\n{code.strip()}\n\n"
        else:
            final_code = str(state.generated_code).strip()

        print("Final Code to Save:")
        print(final_code)

        state = state.model_copy(update={"finale_code": final_code})
        return "generate_test_cases"

    print("⚠️ Security Issues Found! Re-running Code Generation with feedback:")
    print(state.feedback)
    state = state.model_copy(update={"feedback": state.feedback})
    return "orchestrate_code_generation"


