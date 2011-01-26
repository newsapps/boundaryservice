from boundaries.configs.common.settings import *

# Debugging
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Database
DATABASE_HOST = 'TODO'
DATABASE_PORT = '5432'
DATABASE_USER = 'boundaries'
DATABASE_PASSWORD = 'TODO'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://TODO/boundaries/'
ADMIN_MEDIA_PREFIX = 'http://TODO/boundaries/admin_media/'

# Predefined domain
MY_SITE_DOMAIN = 'TODO'

# Email
EMAIL_HOST = 'TODO'
EMAIL_PORT = 25

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'TODO:11211',
    }
}
# S3
AWS_S3_URL = 's3://TODO/boundaries/'

API_DOMAIN = 'TODO'

# logging
import logging.config
LOG_FILENAME = os.path.join(os.path.dirname(__file__), 'logging.conf')
logging.config.fileConfig(LOG_FILENAME)
