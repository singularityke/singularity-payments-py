from pydantic import BaseModel

class MpesaBaseModel(BaseModel):
    """
    Base Pydantic model for all M-Pesa data models.

    This class sets default configuration for all child models:
        - Allows both PascalCase and snake_case field names.
        - Permits extra fields in input data, enabling compatibility with new or unexpected M-Pesa API fields.
    """
    model_config = {
        "populate_by_name": True,  # Allows using PascalCase and snake_case
        "extra": 'allow'  # Allows M-Pesa to send new/unexpected fields
    }
    
 