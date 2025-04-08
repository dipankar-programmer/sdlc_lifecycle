import streamlit as st
import requests
import logging
import ast
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize state management
STATE_DEFAULTS = {
    "feedback_iteration": 0,
    "last_generated_story": None,
    "feedback_history": [],
    "current_user_stories": None,
    "show_feedback_form": False,
    "product_owner_review": False,
    "feedback_form_shown": False,
    "workflow_stage": "init"
}

# Initialize state
for key, default_value in STATE_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


def display_streamed_output(response):
    """Display streaming output and handle state transitions"""
    st.subheader("📤 AI Workflow Output")
    output_container = st.empty()
    full_output = ""
    needs_review = False

    try:
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                logger.debug(f"Received line: {decoded}")
                
                try:
                    data = ast.literal_eval(decoded)
                    
                    # Handle user story generation
                    if 'auto_gen_us' in data:
                        new_story = data['auto_gen_us']['user_stories']
                        st.session_state.last_generated_story = new_story
                        st.session_state.workflow_stage = "story_generated"
                        logger.debug(f"New user story generated: {new_story}")
                    
                    # Handle product owner review
                    if 'product_owner_review' in data:
                        needs_review = True
                        user_stories = data['product_owner_review']['user_stories']
                        logger.debug(f"Updating user stories to: {user_stories}")
                        
                        st.session_state.update({
                            "current_user_stories": user_stories,
                            "show_feedback_form": True,
                            "product_owner_review": True,
                            "workflow_stage": "awaiting_review"
                        })
                        
                        # Track history
                        st.session_state.feedback_history.append({
                            'story': user_stories,
                            'iteration': st.session_state.feedback_iteration,
                            'timestamp': str(datetime.now())
                        })
                        
                except (ValueError, SyntaxError) as e:
                    logger.debug(f"Not JSON data: {e}")
                
                full_output += decoded + "\n"
                output_container.code(full_output, language="text")

        if needs_review and st.session_state.workflow_stage == "awaiting_review":
            logger.debug(f"Story review needed. Iteration: {st.session_state.feedback_iteration}")
            st.rerun()
            
        return needs_review

    except Exception as e:
        logger.error(f"Error in stream processing: {str(e)}")
        st.error(f"Error processing stream: {e}")
        return False


def collect_user_story_feedback():
    """Collect feedback for user stories"""
    logger.debug("Starting feedback collection")
    
    if not st.session_state.current_user_stories:
        logger.warning("No user stories found in session state")
        return None
        
    st.markdown("### Current User Stories")
    st.markdown(st.session_state.current_user_stories)
    
    # Show feedback history
    if st.session_state.feedback_history:
        with st.expander("View Feedback History"):
            for entry in st.session_state.feedback_history:
                st.markdown(f"**Iteration {entry['iteration']}**")
                if entry.get('feedback'):
                    st.markdown(f"*Feedback:* {entry['feedback']}")
                st.markdown("---")
    
    approval = st.radio("Do you approve these user stories?", ["Yes", "No"])
    feedback_text = ""
    
    if approval == "No":
        feedback_text = st.text_area(
            "What improvements are needed?",
            placeholder="Please specify needed improvements",
            height=100,
            key=f"feedback_{st.session_state.feedback_iteration}"
        )
        
        if feedback_text.strip():
            st.session_state.workflow_stage = "feedback_provided"
            st.session_state.feedback_iteration += 1
            
            # Store feedback in history
            st.session_state.feedback_history[-1]['feedback'] = feedback_text
    
    # Return consistent feedback structure
    feedback_data = {
        "approved": approval == "Yes",
        "feedback": feedback_text if approval == "No" else "",
        "user_stories_feedback": "Approved" if approval == "Yes" else f"reject: {feedback_text}",
        "iteration": st.session_state.feedback_iteration,
        "previous_story": st.session_state.last_generated_story,
        "status": "completed"
    }
    
    logger.debug(f"Generated feedback data: {feedback_data}")
    return feedback_data


