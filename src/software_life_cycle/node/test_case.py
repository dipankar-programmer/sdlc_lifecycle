from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from software_life_cycle.state.state import SoftwareLifecycle
from software_life_cycle.LLM.llm import llm_coder
from langgraph.graph import END
from software_life_cycle.utils.batching import chunk_generated_code


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


#step 9: testcase geenration
def generate_test_cases(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """Generates structured test cases based on requirements and previous feedback."""
    print("*" * 50 + " TEST CASE GENERATION " + "*" * 50)

    if not state.generated_code:
        print("No generated code available. Skipping test case generation.")
        return state

    # Chunk the generated code to avoid token overflow
    chunks = chunk_generated_code(state.generated_code, token_limit=5500)
    test_case_results = []

    for idx, chunk in enumerate(chunks):
        prompt_content = f"Generate structured test cases for the following code chunk (Batch {idx+1}):\n{chunk}\n\n"
        
        if state.test_case_feedback.strip() and state.test_case_feedback != "No test case feedback yet.":
            print("THE REVIEW AND THE CHANGES:")
            print(state.test_case_feedback)
            prompt_content += f"Additionally, apply the following **test case feedback** from previous reviews:\n{state.test_case_feedback}\n\n"
            prompt_content += "Ensure missing test cases are added and existing ones are refined."

        messages = [
            SystemMessage(content="You are a senior software engineer. Your task is to create structured unit test cases."),
            HumanMessage(content=prompt_content + """
                                **Instructions:**
                                Generate executable unit test cases for the above code. Use `pytest` or `unittest` conventions depending on the language. Include:
                                - Well-structured, named test functions
                                - Edge case coverage
                                - Error handling validation

                                **Response Format:**
                                - ### Decision: approve/revise
                                - ### Feedback:
                                - Bullet points listing improvements (if any)
                                - ### Structured Unit Test Code:"""
                                )
        ]

        response = llm_coder.invoke(messages).content.strip()
        print(f" Test Cases Generated for Chunk {idx+1}")
        test_case_results.append(response)

    combined_test_case_response = "\n\n".join(test_case_results)

    # Store structured test cases in state
    state = state.model_copy(update={"test_cases": combined_test_case_response})
    return state


#step 10: testcase review code

def review_test_cases(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """AI reviews the generated test cases and decides whether to approve or request changes."""
    print("*" * 50 + f" AI TEST CASE REVIEW (Attempt {state.test_review_attempt + 1}/3) " + "*" * 50)

    if not state.test_cases:
        print(" No test cases available for review.")
        return state

    # Convert test cases string into a dict-like structure so we can chunk it
    fake_code_dict = {"test_cases": state.test_cases}
    chunks = chunk_generated_code(fake_code_dict, token_limit=5500)

    all_feedback = []

    for i, chunk in enumerate(chunks):
        print(f" Sending chunk {i+1}/{len(chunks)} to LLM...")
        chunk_content = "\n\n".join(str(v) for v in chunk.values())

        messages = [
            SystemMessage(content="You are a senior QA engineer. Your task is to review the generated test cases."),
            HumanMessage(content=f"""Here are the test cases (Chunk {i+1}):\n{chunk_content}\n\n
                                    **Review Criteria:**
                                    ✅ Completeness (Do test cases cover all functionalities?)
                                    ✅ Correctness (Are expected results correct?)
                                    ✅ Edge Cases (Are boundary conditions tested?)
                                    ✅ Security (Do test cases validate security concerns?)

                                    **Response Format:**
                                    - Decision: ('approve' or 'revise')
                                    - Feedback: Bullet points explaining necessary improvements, 
                                      make sure to keep the feedback extremely concise and clear
                                    """)
        ]

        response = llm_coder.invoke(messages).content.strip()
        all_feedback.append(f"[Chunk {i+1} Review]: {response}")

    full_review = "\n\n".join(all_feedback)
    print(f"🔍 LLM Combined Test Case Review:\n{full_review}")

    # Append review to feedback
    updated_test_case_feedback = state.test_case_feedback + f"\n[Test Case Review]: {full_review}"
    decision = "revise" if any("revise" in fb.lower() for fb in all_feedback) else "approve"

    return state.model_copy(update={
        "test_review_feedback": decision,
        "test_case_feedback": updated_test_case_feedback,
        "test_review_attempt": state.test_review_attempt + 1
    })


def test_case_review_route(state: SoftwareLifecycle) -> Literal["qa_testing", "generate_test_cases"]:
    """Route based on test case review."""
    print("*" * 50 + " TEST CASE REVIEW DECISION " + "*" * 50)
    
    llm_decision = state.test_review_feedback.strip().lower()

    if state.test_review_attempt >= 2 or "approve" in llm_decision:
        print("Test Cases Approved! Moving to QA Testing.")
        
        # Format and store final test cases
        if isinstance(state.test_cases, str):
            # Extract clean test code
            test_blocks = state.test_cases.split("```")
            clean_tests = ""
            for block in test_blocks:
                if block.strip() and not block.strip().lower() in ['python', 'test']:
                    clean_tests += f"{block.strip()}\n\n"
            
            # Update state with formatted test cases
            state = state.model_copy(update={
                "final_test_cases": clean_tests.strip()
            })
            print(" Saved final test cases")
        return "qa_testing"

    print("Test Cases Need Revision! Re-running Generation.")
    return "generate_test_cases"
