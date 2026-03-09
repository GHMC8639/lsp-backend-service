from pydantic import BaseModel, Field, ConfigDict

# Single reference item
class ReferenceItem(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    mobile_number: str = Field(min_length=10, max_length=15)
    relation_type: str = Field(min_length=2, max_length=50)
    is_emergency_contact: bool


# Payload with two references
class LoanApplicationReferencesCreate(BaseModel):
    reference1: ReferenceItem
    reference2: ReferenceItem

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reference1": {
                    "name": "Ramesh Kumar",
                    "mobile_number": "9876543210",
                    "relation_type": "Friend",
                    "is_emergency_contact": True
                },
                "reference2": {
                    "name": "Suresh Rao",
                    "mobile_number": "9123456789",
                    "relation_type": "Colleague",
                    "is_emergency_contact": False
                }
            }
        }
    )


# Response
class LoanApplicationReferenceResponse(BaseModel):
    id: int
    name: str
    mobile_number: str
    relation_type: str
    is_emergency_contact: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
