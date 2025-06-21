import platform

def get_platform_config():
    return {
        'win': platform.system() == 'Windows',
        'mac': platform.system() == 'Darwin',
        'shell': 'cmd' if platform.system() == 'Windows' else 'bash',
        'ping_args': '-n' if platform.system() == 'Windows' else '-c'
    }