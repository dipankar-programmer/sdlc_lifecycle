from langchain_core.messages import HumanMessage, SystemMessage
from software_life_cycle.state.state import SoftwareLifecycle
from typing import Literal
from software_life_cycle.LLM.llm import llm_docs

#step 4: create design document for functional and technical
def create_design_doc(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """Generate a revised design document based on user stories and design feedback."""
    #print("*" * 50 + " GENERATING DESIGN DOCUMENT " + "*" * 50)

    if not state.user_stories:
        print("User stories missing. Cannot generate design document.")
        return state

    # Base prompt
    base_content = "\n".join([
        "# Design Document Template",
        "",
        "Create a detailed design document for these user stories:",
        state.user_stories,
        "",
        "## Important Rules",
        "- Do not include any testing sections",
        "- Do not include error handling unless explicitly requested",
        "- Use markdown formatting",
        "",

    ])

    # Add feedback if available
    if hasattr(state, 'design_feedback') and state.design_feedback != "No design feedback yet.":
        base_content += "\n\n## Previous Feedback\n" + state.design_feedback
        base_content += "\n\nEnsure all feedback is incorporated and remove any mentioned sections."

    messages = [
        SystemMessage(content="\n".join([
            "You are a software architect creating clear, structured design documents.",
            "Focus on practical, implementable designs.",
            "Use markdown formatting for better readability.",
            "Strictly follow the requested sections only.",
            "Remove any sections mentioned in feedback."
        ])),
        HumanMessage(content=base_content)
    ]

    try:
        # Generate design document
        revised_design = llm_docs.invoke(messages).content
        print("Design Document Generated!")

        # Store the updated design document
        return state.model_copy(update={
            "design_documents": revised_design,
            "design_attempt": getattr(state, 'design_attempt', 0) + 1
        })

    except Exception as e:
        print(f"\nError generating design document: {str(e)}")
        return state


#step 5: create a design review
def design_review(state: SoftwareLifecycle) -> SoftwareLifecycle:
  """Review design documents and approve or reject them."""
  pass


def design_route(state: SoftwareLifecycle) -> Literal["orchestrate_code_generation", "create_design_doc"]:
    """LLM decision determines if the design is accepted or needs revision."""
    #print("*" * 50 + " DESIGN REVIEW " + "*" * 50)

    while True:
        feedback = input("Approve the design? (yes/no): ").strip().lower()

        if feedback in ["yes", "y"]:
            print("Approved! Proceeding to code generation.")
            return "orchestrate_code_generation"

        elif feedback in ["no", "n"]:
            user_feedback = input("Provide design feedback: ").strip()

            # Store design feedback separately
            updated_design_feedback = state.design_feedback + f"\n[Design Review]: {user_feedback}"
            state = state.model_copy(update={"design_feedback": updated_design_feedback})

            print(f"Design rejected! Updating design with feedback:\n{state.design_feedback}")
            return "create_design_doc"

        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
