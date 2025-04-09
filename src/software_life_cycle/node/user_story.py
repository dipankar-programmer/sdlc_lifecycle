from langchain_core.messages import HumanMessage, SystemMessage
from software_life_cycle.state.state import SoftwareLifecycle
from software_life_cycle.LLM.llm import llm
from typing import Literal

# Step 1: taking the input from the user
def input_requirements(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """Collect project requirements from user input."""
    #("\n" + "=" * 20 + " INPUT REQUIREMENTS " + "=" * 20)
    if not state.requirements:
        state.requirements = input("Enter project requirements: ")
    return state.model_copy(update={"requirements": state.requirements})


# Step 2: making the user stories
def auto_gen_us(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """Generate user stories with feedback incorporation"""
    #print("\n" + "=" * 20 + " USER STORY GENERATION " + "=" * 20)

    base_prompt = [
        "Generate a detailed user story with:",
        "1. User Story (As a [role], I want [feature], so that [benefit])",
        "2. Acceptance Criteria (numbered list)",
        "3. Error Handling Scenarios (must include):",
        "   - System errors",
        "   - User input errors",
        "   - Network/resource errors",
        "4. Definition of Done",
        f"\nRequirements: {state.requirements}"
    ]

    if state.user_stories_feedback != "No user story feedback yet.":
        feedback = state.user_stories_feedback
        if "reject:" in feedback:
            feedback = feedback.replace("reject:", "").strip()
            print(f"Processing Feedback: {feedback}")
            
            base_prompt.extend([
                "\nPrevious Story:",
                state.user_stories,
                "\nFeedback to address:",
                feedback,
                "\nRevision Guidelines:",
                "1. Address the feedback completely",
                "2. Maintain existing good elements",
                "3. Include specific error scenarios",
                "4. Ensure measurable acceptance criteria"
            ])

    messages = [
        SystemMessage(content="\n".join([
            "You are an expert Agile coach specializing in user story creation.",
            "Focus on creating comprehensive stories with error handling.",
            "Each revision should improve upon the previous version."
        ])),
        HumanMessage(content="\n".join(base_prompt))
    ]

    try:
        revised_story = llm.invoke(messages).content
        #print("\nGenerated User Story:\n")
        #print(revised_story)

        # Update state with new story
        return state.model_copy(update={
            "user_stories": revised_story,
            "feedback": "Story generated successfully"
        })
    except Exception as e:
        print(f"Error in story generation: {e}")
        return state.model_copy(update={
            "feedback": f"Error in story generation: {str(e)}"
        })


# Step 3: Product owner review (manual CLI feedback)
def product_owner_review(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """Handle product owner review process"""
    return state

# Step 3.1: Routing based on feedback
def product_routing_cond(state: SoftwareLifecycle) -> Literal["create_design_doc", "auto_gen_us"]:
    print("*" * 50 + " PRODUCT OWNER ROUTING " + "*" * 50)
    #print(f"Current User Story: {state.user_stories}")

    while True:
        feedback = input("Do you approve the user story? (yes/no): ").strip().lower()

        if feedback in ["yes", "y"]:
            print("Approved! Returning: create_design_doc")
            return "create_design_doc" 

        elif feedback in ["no", "n"]:
            user_feedback = input("Provide feedback: ").strip()
            print("Rejected! Returning: auto_gen_us")
            updated_userstories_feedback = state.user_stories_feedback + f"\n[Design Review]: {user_feedback}"
            state = state.model_copy(update={"user_stories_feedback": updated_userstories_feedback})
            return "auto_gen_us"

        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
           
