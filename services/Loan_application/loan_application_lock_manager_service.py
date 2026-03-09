from datetime import datetime, timezone
from models.Loan_application.loan_application import LoanApplication


class ApplicationLockManager:

    @staticmethod
    def lock_application(application: LoanApplication):

        now = datetime.now(timezone.utc)

        # Lock main application
        application.is_locked = True
        application.locked_at = now

        # Lock declaration
        if getattr(application, "declaration", None):
            application.declaration.is_locked = True
            application.declaration.locked_at = now

        # Lock references
        if getattr(application, "references", None):
            for ref in application.references:
                ref.is_locked = True
                ref.locked_at = now

        # Lock purpose
        if getattr(application, "purpose", None):
            application.purpose.is_locked = True
            application.purpose.locked_at = now
