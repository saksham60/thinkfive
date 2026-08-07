from case.app.errors import fail


class AuthorizationPolicy:
    REVIEW_ROLES = {"HUMAN_REVIEWER", "SUPERVISOR", "ADMIN"}

    def __init__(self, enforce: bool = True) -> None:
        self.enforce = enforce

    def can_review(self, requested_by: str, reviewed_by: str, reviewer_role: str) -> None:
        if not reviewed_by:
            raise fail("UNAUTHORIZED", "A human reviewer identity is required.")
        if self.enforce and reviewer_role not in self.REVIEW_ROLES:
            raise fail("FORBIDDEN", "Reviewer role is not authorized for approvals.")
        if self.enforce and requested_by == reviewed_by:
            raise fail("SELF_APPROVAL_FORBIDDEN", "The requesting actor cannot approve their own sensitive action.")
