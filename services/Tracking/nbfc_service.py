from services.Tracking.status_update_service import StatusUpdateService


class NBFCService:

    @staticmethod
    def manual_update(db, application_id: str, new_status: str, metadata: dict | None = None):
        return StatusUpdateService.update_status(
            db=db,
            application_id=application_id,
            new_status=new_status,
            source="nbfc_manual",
            metadata=metadata
        )
