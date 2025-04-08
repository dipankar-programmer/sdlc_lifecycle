from langchain_core.messages import HumanMessage, SystemMessage
from software_life_cycle.state.state import SoftwareLifecycle
from typing import Literal
from software_life_cycle.LLM.llm import llm_docs, llm_coder


#step 6: generate the code form design docs
def generate_worker_roles(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """AI dynamically determines required worker roles based on design docs and stores them in state."""
    print("*" * 50, "WORKER ROLE IDENTIFICATION", "*" * 50)

    if not state.design_documents:
        print("Missing design documents. Worker role assignment aborted.")
        return state

    messages = [
        SystemMessage(content="You are a highly experienced software architect. "
                              "Your task is to identify ONLY software development roles required to implement the system. "
                              "DO NOT include roles related to Testing, QA, Technical Writing, DevOps, Management, Project Management, "
                              "Scrum Master, UX/UI, Product Owner, Business Analyst, or any non-development role. "
                              "Your response should ONLY include job titles related to hands-on coding and software development."),
        HumanMessage(content=f"Analyze the following design document:\n\n"
                             f"{state.design_documents}\n\n"
                             "Identify ONLY the software development roles (Backend, Frontend, AI Engineer, Database Engineer, etc.) "
                             "without listing any testing, documentation, or management roles. "
                             "Provide a structured list, one role per line, without explanations."),
    ]

    worker_roles = llm_docs.invoke(messages).content
    worker_roles_dict = {role.strip(): f"Generate code for {role} \n" for role in worker_roles.split("\n") if role.strip()}

    print(f"Assigned Worker Roles: {list(worker_roles_dict.keys())}")

    # Store worker roles in state
    state = state.model_copy(update={"worker_tasks": worker_roles_dict})
    return state


def orchestrate_code_generation(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """Assigns worker roles and tasks dynamically based on AI-generated roles."""
    print("*" * 50, "ORCHESTRATOR: CODE GENERATION", "*" * 50)

    state = generate_worker_roles(state)

    if not state.worker_tasks:
        print("No worker roles found. Skipping code generation.")
        return state

    # Include accumulated feedback in worker tasks
    state.worker_tasks = {
        role: state.design_documents + f"\n{task_desc}\n\n[Accumulated Feedback]: {state.feedback}"
        for role, task_desc in state.worker_tasks.items()
    }

    print(f"Workers Assigned: {list(state.worker_tasks.keys())}")
    return state

def dynamic_worker(task: str, role: str) -> str:
    """Generic worker node that generates code for the assigned role."""
    print(f"-" * 50, f"{role.upper()} CODE GENERATION", "-" * 50)

    messages = [
        SystemMessage(content=f"You are a {role} engineer. Generate optimized and structured code."),
        HumanMessage(content=task),
    ]

    generated_code = llm_coder.invoke(messages).content
    print(f"{role.capitalize()} Code Generated!")
    print(f"{role.capitalize()} Code Generated:\n{generated_code}\n")
    return generated_code


def collect_code_results(state: SoftwareLifecycle) -> SoftwareLifecycle:
    """Collects code from dynamically assigned workers."""
    print("*" * 50, "COLLECTING GENERATED CODE", "*" * 50)

    if not state.worker_tasks:
        print("No assigned worker tasks found. Skipping code collection.")
        return state

    generated_code = {role: dynamic_worker(task, role) for role, task in state.worker_tasks.items()}

    # Store generated code in state
    state = state.model_copy(update={"generated_code": generated_code})
    print(f"Collected Generated Code: {list(generated_code.keys())}")
    print("Code Generation Completed Successfully!")
    return state
