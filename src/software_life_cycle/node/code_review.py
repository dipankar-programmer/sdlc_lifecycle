from langchain_core.messages import HumanMessage, SystemMessage
from software_life_cycle.state.state import SoftwareLifecycle
from software_life_cycle.LLM.llm import llm_coder
from typing import Literal
import json
import re
from software_life_cycle.utils.batching import chunk_generated_code

llm = llm_coder
# def batch_code_for_review(code_dict: dict, token_limit: int = 5500) -> dict:
#     """Split code into batches if it exceeds token limit, otherwise return as is."""
#     # Estimate tokens (roughly 4 chars per token)
#     total_chars = sum(len(str(code)) for code in code_dict.values())
#     estimated_tokens = total_chars // 4
    
#     if estimated_tokens <= token_limit:
#         return code_dict
        
#     # If exceeds limit, split into smaller batches
#     batches = {}
#     current_chars = 0
#     current_batch = {}
    
#     for role, code in code_dict.items():
#         code_chars = len(str(code))
#         if current_chars + code_chars > (token_limit * 4):  # Convert token limit to chars
#             if current_batch:  # Save current batch if not empty
#                 batch_key = f"Batch_{len(batches)}"
#                 batches[batch_key] = current_batch
#                 current_batch = {}
#                 current_chars = 0
        
#         current_batch[role] = code
#         current_chars += code_chars
    
#     # Add final batch if exists
#     if current_batch:
#         batch_key = f"Batch_{len(batches)}"
#         batches[batch_key] = current_batch
    
#     return batches if batches else code_dict

#step 7: review the generated code
# def code_review(state: SoftwareLifecycle) -> SoftwareLifecycle:
#     """AI reviews the generated code and decides whether to approve or request changes."""
#     print("*" * 50 + f" AI CODE REVIEW (Attempt {state.code_review_attempt + 1}/3) " + "*" * 50)

#     if not state.generated_code:
#         print("No generated code available for review.")
#         return state

#     code_batches = batch_code_for_review(state.generated_code, token_limit=5800)  # keep it under 6k TPM limit

#     if isinstance(code_batches, dict) and any("Batch_" in key for key in code_batches):
#         print("Large code detected. Splitting into safe-size batches...")
#         batch_reviews = []
#         for batch_key, batch_code in code_batches.items():
#             batch_prompt = f"### Code Review Batch: {batch_key}\n{json.dumps(batch_code, indent=2)}\n\n"
#             if state.feedback.strip():
#                 batch_prompt += f"Previous Feedback:\n{state.feedback.strip()}\n"

#             messages = [
#                 SystemMessage(content="You are an expert software reviewer. Review code for correctness, efficiency, maintainability, and security."),
#                 HumanMessage(content=batch_prompt)
#             ]
#             try:
#                 response = llm.invoke(messages).content.strip()
#                 batch_reviews.append(f"[{batch_key}]: {response}")
#             except Exception as e:
#                 print(f"Error in LLM for {batch_key}: {e}")
#                 batch_reviews.append(f"[{batch_key}]: ERROR during review")

#         ai_response = "\n\n".join(batch_reviews)
#     else:
#         # Small enough to send all at once
#         code_content = json.dumps(state.generated_code, indent=2)
#         prompt_content = f"Here is the generated code:\n{code_content}\n"
#         if state.feedback.strip():
#             prompt_content += f"\nPrevious Feedback:\n{state.feedback.strip()}\n"

#         messages = [
#             SystemMessage(content="You are an expert software reviewer. Review code for correctness, efficiency, maintainability, and security."),
#             HumanMessage(content=prompt_content)
#         ]
#         try:
#             ai_response = llm.invoke(messages).content.strip()
#         except Exception as e:
#             print(f"Error during review: {e}")
#             ai_response = "ERROR"

#     print(f"🔍 LLM Code Review Decision:\n{ai_response}")

#     # Extract decision
#     decision = "revise"
#     if "approve" in ai_response.lower():
#         decision = "approve"

#     updated_feedback = state.feedback + f"\n[Code Review Attempt {state.code_review_attempt + 1}]: {ai_response}"

#     return state.model_copy(update={
#         "code_review_feedback": decision,
#         "feedback": updated_feedback,
#         "code_review_attempt": state.code_review_attempt + 1
#     })
def code_review(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """AI reviews the generated code and decides whether to approve or request changes."""
    print("*" * 50 + f" AI CODE REVIEW (Attempt {state.code_review_attempt + 1}/3) " + "*" * 50)

    if not state.generated_code:
        print("No generated code available for review.")
        return state

    code_batches = chunk_generated_code(state.generated_code, token_limit=5800)

    if isinstance(code_batches, dict) and any("Batch_" in key for key in code_batches):
        print("Large code detected. Splitting into safe-size batches...")
        batch_reviews = []
        for batch_key, batch_code in code_batches.items():
            batch_prompt = f"### Code Review Batch: {batch_key}\n{json.dumps(batch_code, indent=2)}\n\n"

            if state.feedback.strip():
                batch_prompt += (
                    f"### Previous Feedback:\n{state.feedback.strip()}\n"
                    f"### Please consider this feedback while reviewing the code.\n"
                )

            messages = [
                SystemMessage(content="You are an expert software reviewer. Review code for correctness, efficiency, maintainability, and security."),
                HumanMessage(content=batch_prompt)
            ]
            try:
                response = llm.invoke(messages).content.strip()
                batch_reviews.append(f"[{batch_key}]: {response}")
            except Exception as e:
                print(f"Error in LLM for {batch_key}: {e}")
                batch_reviews.append(f"[{batch_key}]: ERROR during review")

        ai_response = "\n\n".join(batch_reviews)
    else:
        code_content = json.dumps(state.generated_code, indent=2)
        prompt_content = f"Here is the generated code:\n{code_content}\n"

        if state.feedback.strip():
            prompt_content += (
                f"\n### Previous Feedback:\n{state.feedback.strip()}\n"
                f"### Please consider this feedback while reviewing the code.\n"
            )

        messages = [
            SystemMessage(content="You are an expert software reviewer. "
            "Review code for correctness, efficiency, maintainability, and security."
            "make sure to keep the feedback extremely concise and clear"),
            HumanMessage(content=prompt_content)
        ]
        try:
            ai_response = llm.invoke(messages).content.strip()
        except Exception as e:
            print(f"Error during review: {e}")
            ai_response = "ERROR"

    print(f"🔍 LLM Code Review Decision:\n{ai_response}")

    decision = "revise"
    if "approve" in ai_response.lower():
        decision = "approve"

    updated_feedback = state.feedback + f"\n[Code Review Attempt {state.code_review_attempt + 1}]: {ai_response}"

    return state.model_copy(update={
        "code_review_feedback": decision,
        "feedback": updated_feedback,
        "code_review_attempt": state.code_review_attempt + 1
    })


def code_route(state: SoftwareLifecycle) -> Literal["code_security_review", "orchestrate_code_generation"]:
    """LLM decision determines if the code is accepted or needs improvement."""
    print("*" * 50 + " AI CODE REVIEW DECISION " + "*" * 50)

    llm_decision = state.code_review_feedback 

    #Stop reviewing after 3 attempts
    if state.code_review_attempt >= 2:
        print("Maximum security review attempts reached! Accepting the current code.")
        return "code_security_review"

    if "approve" in llm_decision.split("\n")[0]: 
        print("LLM Approved the Code! Moving to Security Review.")
        return "code_security_review"

    elif llm_decision == "revise":
        print("LLM Requested Improvements! Re-running Code Generation.")
        return "orchestrate_code_generation"
    else:
        print("Unexpected LLM response. Defaulting to code improvement.")
        return "orchestrate_code_generation"
