from aiohttp import web

from src.application.app import app_factory


if __name__ == "__main__":
    web.run_app(app_factory())
