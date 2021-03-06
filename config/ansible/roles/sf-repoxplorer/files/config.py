import copy

# RepoXplorer configuration file
base_logging = {
    'version': 1,
    'root': {'level': 'DEBUG', 'handlers': ['normal']},
    'loggers': {
        'indexerDaemon': {
            'level': 'DEBUG',
            'handlers': ['normal', 'console'],
            'propagate': False,
        },
        'repoxplorer': {
            'level': 'DEBUG',
            'handlers': ['normal', 'console'],
            'propagate': False,
        },
        'elasticsearch': {
            'level': 'WARN',
            'handlers': ['normal', 'console'],
            'propagate': False,
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'normal': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'normal',
            'filename': '',
            'when': 'D',
            'interval': 1,
            'backupCount': 30,
        },
    },
    'formatters': {
        'console': {'format': ('%(levelname)-5.5s [%(name)s]'
                    '[%(threadName)s] %(message)s')},
        'normal': {'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                   '[%(threadName)s] %(message)s')},
    }
}

# Internal dev pecan server
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan REST and rendering configuration
app = {
    'root': 'repoxplorer.controllers.root.RootController',
    'modules': ['repoxplorer'],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/templates',
    'debug': True,
    'errors': {
        404: '/error/404',
        '__force_dict__': True
    }
}

# Additional RepoXplorer configurations
projects_file_path = '/etc/repoxplorer/projects.yaml'
idents_file_path = '/etc/repoxplorer/idents.yaml'
git_store = '/var/lib/repoxplorer/git_store'
elasticsearch_host = 'elasticsearch'
elasticsearch_port = 9200
elasticsearch_index = 'repoxplorer'
indexer_loop_delay = 60

# Logging configuration for the wsgi app
logging = copy.deepcopy(base_logging)
logging['handlers']['normal']['filename'] = (
    '/var/log/repoxplorer/repoxplorer-webui-debug.log')

# Logging configuration for the indexer
indexer_logging = copy.deepcopy(base_logging)
indexer_logging['handlers']['normal']['filename'] = (
    '/var/log/repoxplorer/repoxplorer-indexer-debug.log')
