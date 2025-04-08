from typing import Literal
from software_life_cycle.state.state import SoftwareLifecycle
from typing import Literal
from langgraph.graph import END
from langchain_core.messages import HumanMessage, SystemMessage
from software_life_cycle.node.file_saver import save_final_outputs
from software_life_cycle.LLM.llm import llm_coder
from software_life_cycle.utils.batching import chunk_generated_code
import json



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


# Step 11: QA Testing

def qa_testing(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """AI executes test cases on the generated code and determines if any failures occur."""
    print("*" * 50 + f" AI QA TESTING (Attempt {state.qa_attempts + 1}/3) " + "*" * 50)

    if not state.generated_code or not state.test_cases:
        print("Missing generated code or test cases. Skipping QA Testing.")
        return state

    # Estimate token size of test cases and feedback
    estimated_token = lambda text: len(str(text)) // 4
    test_case_tokens = estimated_token(state.test_cases)
    feedback_tokens = estimated_token(state.feedback)

    total_available = 6000
    reserved = test_case_tokens + feedback_tokens + 1000  # 1000 extra for prompt, instructions, metadata
    code_token_limit = max(1000, total_available - reserved)  # Always leave at least 1000 tokens for code

    print(f"📏 Test case tokens: {test_case_tokens}, Feedback tokens: {feedback_tokens}")
    print(f"🧮 Using token limit {code_token_limit} for each code chunk")

    code_chunks = chunk_generated_code(state.generated_code, token_limit=code_token_limit)
    combined_feedback = []

    for idx, chunk in enumerate(code_chunks):
        code_str = json.dumps(chunk, indent=2) if isinstance(chunk, dict) else chunk

        prompt_content = f"""
                You are a QA automation engineer. Execute the following test cases on this code 
                chunk (Batch {idx+1}) and report the result.

                ### Test Cases:
                {state.test_cases}

                ### Code:
                {code_str}
                """

        if state.feedback.strip():
            prompt_content += f"""
                        ### Previous QA Feedback:
                        {state.feedback}

                        Ensure previous issues are re-validated in this batch.
                        """

        messages = [
            SystemMessage(content="You're a senior QA engineer running test suites on submitted code."),
            HumanMessage(content=prompt_content + """
                                    **Response Format:**
                                    - Decision: ('pass' or 'fail')
                                    - Feedback: Bullet points on failures or confirmations of success.
                                    """)
                                            ]

        try:
            response = llm_coder.invoke(messages).content.strip()
            print(f" QA Test Result for Chunk {idx+1}")
            combined_feedback.append(f"[Batch {idx+1} QA Result]:\n{response}")
        except Exception as e:
            print(f" Error during QA test for chunk {idx+1}: {e}")
            combined_feedback.append(f"[Batch {idx+1}]: ERROR during QA test")

    final_feedback = "\n\n".join(combined_feedback)
    print(f" Final QA Decision:\n{final_feedback}")

    decision = "fail" if any("fail" in fb.lower() for fb in combined_feedback) else "pass"
    updated_feedback = state.feedback + f"\n[QA Testing]: {final_feedback}"

    return state.model_copy(update={
        "qa_test_result": decision,
        "feedback": updated_feedback,
        "qa_attempts": state.qa_attempts + 1
    })



def qa_test_route(state: SoftwareLifecycle) -> Literal["END", "orchestrate_code_generation"]:
    """Routes based on QA test results: Pass -> Save Files & END, Fail -> Fix Code."""
    print("*" * 50 + " QA TESTING DECISION " + "*" * 50)

    if not state.qa_test_result:
        print("No QA result found! Defaulting to re-run Code Generation.")
        return "orchestrate_code_generation"

    qa_decision = state.qa_test_result.strip().lower()
    first_line = qa_decision.split("\n")[0]

    if state.qa_attempts >= 1:
        print(" Maximum QA testing attempts reached! Accepting the current version.")
        # print("\nFinal Test Cases in State:")
        # print(state.generated_code or "[empty]")

        # print("\nFinal Code in State:")
        # print(state.test_cases or "[empty]")

        save_final_outputs(state)
        return END

    if "pass" in first_line:
        print("QA Testing Passed! Saving final outputs and completing process.")
        # print("\nFinal Test Cases in State:")
        # print(state.generated_code or "[empty]")

        # print("\nFinal Code in State:")
        # print(state.test_cases or "[empty]")

        save_final_outputs(state)
        return END

    if "fail" in first_line:
        print("QA Testing Failed! Re-running Code Generation for Fixes.")
        return "orchestrate_code_generation"

    print("Unexpected QA response. Defaulting to re-run Code Generation.")
    return "orchestrate_code_generation"