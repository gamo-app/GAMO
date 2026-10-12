from workers import WorkerEntrypoint, asgi

from app import app
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request.js_object, self.env)