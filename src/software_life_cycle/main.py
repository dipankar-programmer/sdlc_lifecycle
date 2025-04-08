import typer
import uuid
import json
import hashlib
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from software_life_cycle.graph.builder import graph
from software_life_cycle.state.state import SoftwareLifecycle
import time
console = Console()
app = typer.Typer()
displayed_content = set()

# ---------- Utility Functions (Same as before) ----------

def format_dict_to_markdown(content: dict) -> str:
    markdown_content = []
    for key, value in content.items():
        if isinstance(value, str):
            markdown_content.append(f"## {key.replace('_', ' ').title()}\n\n{value}\n")
        elif isinstance(value, dict):
            markdown_content.append(f"## {key.replace('_', ' ').title()}\n")
            for sub_key, sub_value in value.items():
                markdown_content.append(f"### {sub_key.replace('_', ' ').title()}\n\n{sub_value}\n")
        elif isinstance(value, (list, tuple)):
            markdown_content.append(f"## {key.replace('_', ' ').title()}\n")
            for item in value:
                markdown_content.append(f"* {item}\n")
    return "\n".join(markdown_content)

def format_node_content(operation: str, content: dict) -> str:
    if operation == "auto_gen_us":
        return content.get('user_stories', '')
    elif operation == "create_design_doc":
        return content.get('design_documents', '')
    elif operation == "qa_testing":
        test_cases = content.get('test_cases', '')
        results = content.get('qa_test_result', '')
        feedback = content.get('test_review_feedback', '')
        attempts = content.get('qa_attempts', 0)

        qa_report = [
            "# QA Testing Report",
            "",
            "## Test Execution Results",
            f"**Status:** {results.upper() if results else 'No results'}",
            "",
            "## Test Cases Executed",
            f"```python\n{test_cases.strip()}\n```" if test_cases else "No test cases available",
            "",
            "## Issues Identified",
            f"- {feedback}" if feedback and feedback.lower() != "approved" else "No issues reported",
            "",
            "## Test Execution Details",
            f"**Attempt:** {attempts}",
            f"**Last Run:** {'Yes' if test_cases else 'No'}"
        ]
        return "\n".join(qa_report)

    elif operation == "security_review":
        feedback = content.get('security_feedback', '')
        attempts = content.get('code_security_attempt', 0)
        security_report = [
            "# Security Review Report",
            "",
            "## Security Analysis",
            "### Key Findings",
            feedback if feedback else "No security feedback available",
            "",
            "## Review Details",
            f"**Review Attempt:** {attempts}",
            f"**Status:** {'In Progress' if feedback == 'fix' else 'Complete'}"
        ]
        return "\n".join(security_report)
    elif operation == "code_review":
        feedback = content.get('code_review_feedback', '')
        code = content.get('generated_code', '')
        attempts = content.get('code_review_attempt', 0)
        if isinstance(code, dict):
            code_content = ""
            for role, text in code.items():
                if 'code' in text.lower() or 'implementation' in text.lower():
                    code_content = text.split('```python')[-1].split('```')[0].strip()
                    break
            code = code_content if code_content else json.dumps(code, indent=2)
        code_review = [
            "# Code Review Report",
            "",
            "## Review Analysis",
            feedback if feedback else "No code review feedback available",
            "",
            "## Implementation Status",
            f"**Attempt:** {attempts}",
            f"**Status:** {'Needs Revision' if feedback == 'revise' else 'Approved'}",
            "",
            "## Code Implementation",
            "```python",
            code if code else "# No code available",
            "```"
        ]
        return "\n".join(code_review)
    elif operation == "test_case_generation":
        test_cases = content.get('test_cases', '')
        feedback = content.get('test_case_feedback', '')
        attempts = content.get('test_review_attempt', 0)
        if isinstance(test_cases, dict):
            test_cases = json.dumps(test_cases, indent=4)
        test_report = [
            "# Test Case Generation Report",
            "",
            "## Generated Test Suite",
            str(test_cases) if test_cases else "No test cases available",
            "",
            "## Coverage Analysis",
            str(feedback) if feedback else "No coverage information available",
            "",
            "## Generation Details",
            f"**Attempt:** {attempts}",
            f"**Status:** {'Complete' if test_cases else 'Pending'}"
        ]
        return "\n".join(test_report)
    else:
        return format_dict_to_markdown(content)

def get_content_hash(content: any) -> str:
    try:
        if isinstance(content, dict):
            content = json.dumps(content, sort_keys=True)
        elif not isinstance(content, str):
            content = str(content)
        return hashlib.md5(content.encode()).hexdigest()
    except Exception as e:
        print(f"Could not hash content ({type(content)}):", e)
        return str(uuid.uuid4())  # fallback hash


def display_content(content: any, style: str = "white", title: str = None, operation: str = None) -> None:
    if not content:
        return
    content_hash = get_content_hash(content)
    if content_hash in displayed_content:
        return
    displayed_content.add(content_hash)
    if isinstance(content, dict) and operation:
        formatted_content = format_node_content(operation, content)
    elif isinstance(content, dict):
        formatted_content = format_dict_to_markdown(content)
    else:
        formatted_content = str(content)
    if "```" in formatted_content:
        sections = formatted_content.split("```")
        for i, section in enumerate(sections):
            if i % 2 == 0:
                if section.strip():
                    console.print(Panel(Markdown(section.strip()), style=style, expand=True))
            else:
                lines = section.split('\n')
                lang = lines[0].strip().lower()
                code = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                if lang in ['python', 'java', 'javascript', 'typescript', 'cpp', 'c++']:
                    code_chunks = code.split('\n\n')
                    for chunk in code_chunks:
                        if chunk.strip():
                            console.print(Panel(Syntax(chunk.strip(), lang, theme="monokai", word_wrap=True, line_numbers=True), title=f"📝 {lang.upper()} Implementation", style="cyan", expand=True))
                else:
                    console.print(Panel(Syntax(code.strip(), "text", theme="monokai"), title=f"📝 Code Implementation", style="cyan", expand=True))
    else:
        console.print(Panel(Markdown(formatted_content), title=title if title else "", style=style, expand=True))

def display_final_results(state: SoftwareLifecycle):
    console.print("\n\n" + "="*50 + "\nFINAL DELIVERABLES\n" + "="*50)
    if isinstance(state.finale_code, str) and state.finale_code.strip():
        console.print("\n" + "="*30 + " FINAL CODE " + "="*30)
        code_sections = state.finale_code.split("\n\n")
        for section in code_sections:
            if section.strip():
                console.print(Panel(Syntax(section.strip(), "python", theme="monokai", line_numbers=True, word_wrap=True), title="📝 PYTHON Implementation", style="cyan", expand=True, padding=(1, 2)))
    if isinstance(state.final_test_cases, str) and state.final_test_cases.strip():
        console.print("\n" + "="*30 + " 🧪 TEST SUITE " + "="*30)
        test_sections = state.final_test_cases.split("\n\n")
        for section in test_sections:
            if section.strip():
                console.print(Panel(Syntax(section.strip(), "python", theme="monokai", line_numbers=True, word_wrap=True), title="🧪 Test Implementation", style="blue", expand=True, padding=(1, 2)))
    console.print("\n" + "="*50)
    console.print("✨ End of Implementation", style="bold green")

# ---------- CLI Entry Point ----------

@app.command()
def run(requirements: str = typer.Option(..., prompt="Enter project requirements")):
    """Run the full AI SDLC workflow with LangGraph from the command line."""
    try:
        start_time = time.time()


        displayed_content.clear()
        state = SoftwareLifecycle(
            requirements=requirements,
            design_attempt=0,
            design_feedback="No design feedback yet.",
            status="pending",
            user_stories_feedback="",
            finale_code="",
            final_test_cases=""
        )
        thread_id = str(uuid.uuid4())
        console.print(Panel(f"{requirements}", title=" Starting Workflow", style="blue"))

        for chunk in graph.stream(state, config={"configurable": {"thread_id": thread_id}}):
            operation = list(chunk.keys())[0]
            content = chunk[operation]
            if isinstance(content, str) and ('=' * 10 in content or '📢' in content):
                continue
            if operation == "auto_gen_us":
                story = content.get('user_stories', '')
                display_content(story, "green", "📝 User Story", operation)
            elif operation == "product_owner_review":
                actual_status = content.get('status', 'pending')
                display_status = "Approved" if actual_status == "approved" else "Changes Requested"
                style = "green" if actual_status == "approved" else "yellow"
                display_content(display_status, style, "👀 Product Owner Review")
            elif operation == "create_design_doc":
                if content.get('design_documents'):
                    display_content(content.get('design_documents'), "cyan", "🏗️ Design Document", operation)
            elif operation == "code_review":
                if content.get('generated_code') or content.get('code_review_feedback'):
                    display_content(content, "yellow", "🔍 Code Review", operation)
            elif operation == "security_review":
                if content.get('security_feedback'):
                    display_content(content, "red", "🔒 Security Review", operation)
            elif operation == "test_case_generation":
                if content.get('test_cases'):
                    display_content(content, "blue", "🧪 Test Cases", operation)
            elif operation == "qa_testing":
                if content.get('qa_test_result'):
                    display_content(content, "magenta", "✅ QA Testing", operation)
            elif operation == "feedback":
                feedback = content.get("feedback", "")
                if feedback and feedback != "No feedback yet.":
                    display_content(feedback, "magenta", "💬 Feedback", operation)

        # Get final updated state
        state = state.model_copy(update={
                "finale_code": state.generated_code,
                "final_test_cases": state.test_cases
            })

        # Show the final output
        display_final_results(state)
        console.print("\n Workflow Complete!", style="bold green")
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\n WORKFLOW COMPLETED IN {elapsed_time/60:.2f} minutes")

    except Exception as e:
        console.print(f"\n Error in workflow: {str(e)}", style="bold red")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(app())


#python -m software_life_cycle.main