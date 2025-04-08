from langgraph.graph import START, StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import display, Image
from software_life_cycle.state.state import SoftwareLifecycle
from software_life_cycle.node.user_story import input_requirements, auto_gen_us, product_owner_review, product_routing_cond
from software_life_cycle.node.design_doc import create_design_doc, design_review, design_route
from software_life_cycle.node.coder import orchestrate_code_generation, collect_code_results
from software_life_cycle.node.code_review import code_review, code_route
from software_life_cycle.node.code_security import code_security_review, security_route
from software_life_cycle.node.test_case import generate_test_cases, review_test_cases, test_case_review_route
from software_life_cycle.node.qa import qa_testing, qa_test_route
import time

builder = StateGraph(SoftwareLifecycle)

builder.add_node("input_requirements", input_requirements)
builder.add_node("auto_gen_us", auto_gen_us)
builder.add_node("product_owner_review", product_owner_review)
builder.add_node("create_design_doc", create_design_doc)
builder.add_node("design_review", design_review)
builder.add_node("orchestrate_code_generation", orchestrate_code_generation)
builder.add_node("collect_code_results", collect_code_results)
builder.add_node("code_review", code_review)
builder.add_node("code_security_review", code_security_review)
builder.add_node("generate_test_cases", generate_test_cases)
builder.add_node("review_test_cases", review_test_cases)
builder.add_node("qa_testing", qa_testing)


# --- Existing Edges ---
builder.add_edge(START, "input_requirements")
builder.add_edge("input_requirements", "auto_gen_us")
builder.add_edge("auto_gen_us", "product_owner_review")

builder.add_conditional_edges(
    "product_owner_review",
    product_routing_cond,
    {"create_design_doc" : "create_design_doc","auto_gen_us" : "auto_gen_us"}
)

# --- Design Review Path ---
builder.add_edge("create_design_doc", "design_review")
builder.add_conditional_edges(
    "design_review",
    design_route,
    {"orchestrate_code_generation": "orchestrate_code_generation", "create_design_doc": "create_design_doc"}
)


builder.add_edge("orchestrate_code_generation", "collect_code_results")  
builder.add_edge("collect_code_results", "code_review")  
builder.add_conditional_edges(
    "code_review",
    code_route,
    {"code_security_review": "code_security_review", "orchestrate_code_generation": "orchestrate_code_generation"}
)
builder.add_conditional_edges(
    "code_security_review",
    security_route,
    {"generate_test_cases": "generate_test_cases", "orchestrate_code_generation": "orchestrate_code_generation"}
)
builder.add_edge("generate_test_cases", "review_test_cases")
builder.add_conditional_edges(
    "review_test_cases",
    test_case_review_route,
    {"qa_testing": "qa_testing", "generate_test_cases": "generate_test_cases"}
)
builder.add_conditional_edges(
    "qa_testing",
    qa_test_route,
    {END: END, "generate_test_cases": "orchestrate_code_generation"}
)

print(" LangGraph Workflow Initializing ")

try:
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    #display(Image(graph.get_graph().draw_mermaid_png()))
    



except Exception as e:
    print("Error Compiling Graph:", str(e))