import pydantic
from pydantic import BaseModel, Field
from typing import Dict, Literal, Optional


class SoftwareLifecycle(BaseModel):
    requirements: str = None
    user_stories: str = None
    design_documents: str = None
    worker_tasks: Dict[str, str] = None
    generated_code: Dict[str, str] = None
    code_review_feedback: Literal["approve", "revise"] = "revise"
    code_review_attempt: int = 0
    security_feedback: Literal["secure", "fix"] = "fix"
    code_security_attempt: int = 0
    test_review_attempt: int = 0
    test_cases: str = None
    feedback: str = "No feedback yet."
    test_review_feedback: Literal["approve", "revise"] = "revise"
    qa_test_result: Literal["pass", "fail"] = "fail"
    qa_attempts: int = 0
    design_attempt: int = Field(default=0)
    design_feedback: str = Field(default="No design feedback yet.")
    status: str = Field(default="pending")
    user_stories_feedback: str = Field(default="")
    test_case_feedback: str = "No test case feedback yet."
    finale_code: Optional[str] = Field(default="")
    final_test_cases: Optional[str] = Field(default="")

    def __hash__(self):
        """Make state hashable for graph operations."""
        return hash((
            self.requirements,
            frozenset(self.generated_code.items()) if isinstance(self.generated_code, dict) else None,
            self.code_review_feedback,
            self.code_review_attempt,
            self.security_feedback,
            self.code_security_attempt
        ))
    
    def __eq__(self, other):
        if not isinstance(other, SoftwareLifecycle):
            return False
        return (
            self.requirements == other.requirements and
            self.generated_code == other.generated_code and
            self.code_review_feedback == other.code_review_feedback and
            self.code_review_attempt == other.code_review_attempt and
            self.security_feedback == other.security_feedback and
            self.code_security_attempt == other.code_security_attempt
        )

