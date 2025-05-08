from talkushka_service.app.handlers.app import app_router
from talkushka_service.app.handlers.create_promocode import create_promocode_router
from talkushka_service.app.handlers.help import cmd_help_router
from talkushka_service.app.handlers.start import cmd_start_router
from talkushka_service.app.handlers.use_promocode import use_promocode_router

routers = [app_router, create_promocode_router, cmd_help_router, cmd_start_router, use_promocode_router]

__all__ = ["routers"]
