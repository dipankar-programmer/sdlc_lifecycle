# workflow.py
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from software_life_cycle.graph.builder import graph
from software_life_cycle.state.state import SoftwareLifecycle
from software_life_cycle.node.user_story import product_routing_cond

router = APIRouter()
global_state = SoftwareLifecycle()

class WorkflowInput(BaseModel):
    requirements: str
    user_stories_feedback: str = "No user story feedback yet."
    feedback_iteration: int = 0
    previous_story: str = ""

class FeedbackInput(BaseModel):
    user_stories_feedback: str
    requirements: str
    feedback_iteration: int

@router.post("/run_ai_workflow/", response_class=StreamingResponse)
def run_ai_workflow(data: WorkflowInput):
    global global_state
    
    # Initialize or update state with complete context
    global_state = SoftwareLifecycle(
        requirements=data.requirements,
        user_stories_feedback=data.user_stories_feedback,
        feedback_iteration=data.feedback_iteration,
        user_stories=data.previous_story  # Preserve previous story
    )
    print(f"Initializing workflow with feedback: {global_state.user_stories_feedback}")
    
    config = {"configurable": {"thread_id": "1"}}

    def stream_generator():
        global global_state
        try:
            for chunk in graph.stream(global_state, config):
                print("🔁 CHUNK:", chunk)
                key = list(chunk.keys())[0]
                
                # Enhanced state preservation
                new_state = chunk[key]
                new_state.update({
                    "user_stories_feedback": global_state.user_stories_feedback,
                    "feedback_iteration": global_state.feedback_iteration,
                    "previous_feedback": global_state.user_stories_feedback,
                })
                
                # Update global state
                global_state = global_state.model_copy(update=new_state)
                print(f"State after update - Feedback: {global_state.user_stories_feedback}")
                print(f"Current iteration: {global_state.feedback_iteration}")
                
                yield f"{chunk}\n"

                if key == "product_owner_review":
                    break

        except Exception as e:
            print(f"Error in workflow: {e}")
            yield f"ERROR:: {str(e)}"

    return StreamingResponse(stream_generator(), media_type="text/plain")

@router.post("/send_feedback/", response_class=StreamingResponse)
def send_feedback(data: FeedbackInput):
    global global_state
    
    # Store feedback before stream starts
    feedback = data.user_stories_feedback
    iteration = data.feedback_iteration
    
    # Create new state with feedback
    global_state = SoftwareLifecycle(
        requirements=data.requirements,
        user_stories=global_state.user_stories,
        user_stories_feedback=feedback,
        feedback_iteration=iteration,
        previous_feedback=global_state.user_stories_feedback
    )
    
    print(f"💬 New feedback received: {feedback}")
    print(f"📝 Previous story: {global_state.user_stories}")
    print(f"🔢 Iteration: {iteration}")

    next_node = product_routing_cond(global_state)
    config = {"configurable": {"thread_id": "1"}}

    def stream_generator():
        global global_state
        try:
            for chunk in graph.stream(global_state, config, start_at=next_node):
                print(f"🔄 Processing chunk: {chunk}")
                key = list(chunk.keys())[0]
                
                # Get new state from chunk
                new_state = chunk[key]
                
                # CRITICAL: Preserve feedback in every state update
                preserved_state = {
                    "user_stories_feedback": feedback,
                    "feedback_iteration": iteration,
                    "previous_feedback": global_state.previous_feedback,
                    "requires_review": True
                }
                
                # Update chunk state with preserved feedback
                new_state.update(preserved_state)
                
                # Update global state
                global_state = SoftwareLifecycle(**new_state)
                print(f"✨ Updated state - Feedback: {global_state.user_stories_feedback}")
                
                yield f"{chunk}\n"

        except Exception as e:
            print(f"❌ Error in feedback stream: {e}")
            yield f"ERROR:: {str(e)}"
            return

    return StreamingResponse(stream_generator(), media_type="text/plain")

