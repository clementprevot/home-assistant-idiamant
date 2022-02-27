"""
Entity class for iDiamant.
"""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION, MANUFACTURER


class IdiamantEntity(CoordinatorEntity):
    """
    The main iDiamant entity class.
    """

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self.config_entry = config_entry

    @property
    def unique_id(self):
        """
        Return a unique ID to use for this entity.
        """

        return self.config_entry.entry_id

    @property
    def device_info(self):
        """
        Return the device information.
        """

        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "manufacturer": MANUFACTURER,
            "model": VERSION,
            "name": NAME,
        }

    @property
    def device_state_attributes(self):
        """
        Return the state attributes.
        """

        return {
            "id": str(self.coordinator.data.get("id")),
            "integration": DOMAIN,
        }
