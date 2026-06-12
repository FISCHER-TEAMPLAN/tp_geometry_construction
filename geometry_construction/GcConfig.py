from dataclasses import dataclass

@dataclass
class GcConfig():
    """Configuration parameters affecting the Behaviour of the library.
    Tools using Geometry Construction might expose some of these values 
    directly or indeirectly
    so the QGIS user is able to alter them according to theire usecase
    """
    default_z_value: float = -99999999
    default_m_value: float = 0

gc_config = GcConfig()