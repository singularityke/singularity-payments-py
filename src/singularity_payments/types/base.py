from pydantic import MpesaBaseModel, ConfigDict


class MpesaMpesaBaseModel(MpesaBaseModel):
    # This config will be inherited by all children
    model_config = ConfigDict(
        populate_by_name=True, # Allows using PascalCase and snake_case
        extra='allow'          # Allows M-Pesa to send new/unexpected fields
    )
