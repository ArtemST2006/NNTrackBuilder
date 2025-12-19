from .start import router as start_router
from .help import router as help_router
from .location import router as location_router
from .auth import router as auth_router
from .route import router as route_router

__all__ = [
    'start_router',
    'help_router', 
    'location_router',
    'auth_router',
    'route_router'
]