from abc import ABC, abstractmethod
from typing import Any, Dict

class NavixPlugin(ABC):
    """
    Base class for all NAVIX V5 Plugins.
    Developers can extend this to add new capabilities to NAVIX.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the plugin."""
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        """The version of the plugin."""
        pass

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Setup plugin resources. Returns True if successful."""
        pass

    @abstractmethod
    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """The core execution logic of the plugin."""
        pass
