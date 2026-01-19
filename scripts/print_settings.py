from app.core.settings import app_settings
import os
print('app_settings.REDIS_URL=', app_settings.REDIS_URL)
print('app_settings.PRESENCE_BACKEND=', app_settings.PRESENCE_BACKEND)
print('ENV REDIS_URL=', os.environ.get('REDIS_URL'))
print('ENV PRESENCE_BACKEND=', os.environ.get('PRESENCE_BACKEND'))
