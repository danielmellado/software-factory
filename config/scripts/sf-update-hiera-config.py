#!/usr/bin/python
# Update hiera configuration with new defaults

from sys import argv
import string
import yaml
import os

DEFAULT_ARCH = "/usr/local/share/sf-default-config/arch.yaml"


def save(name, data):
    filename = "%s/%s.yaml" % (hiera_dir, name)
    if os.path.isfile(filename):
        os.rename(filename, "%s.orig" % filename)
    yaml.dump(data, open(filename, "w"), default_flow_style=False)
    print "Updated %s (old version saved to %s)" % (filename,
                                                    "%s.orig" % filename)


def load(name):
    filename = "%s/%s.yaml" % (hiera_dir, name)
    return yaml.load(open(filename).read())


def update_sfconfig(data):
    dirty = False
    # 2.2.3: remove service list (useless since arch.yaml)
    if 'services' in data:
        del data['services']
        dirty = True

    # Make sure mirrors is in the conf
    if 'mirrors' not in data:
        data['mirrors'] = {
            'swift_mirror_url': 'http://swift:8080/v1/AUTH_uuid/repomirror/',
            'swift_mirror_tempurl_key': 'CHANGEME',
        }
        dirty = True

    # 2.2.4: refactor OAuth2 and OpenID auth config
    if 'oauth2' not in data['authentication']:
        data['authentication']['oauth2'] = {
            'github': {
                'disabled': False,
                'client_id': '',
                'client_secret': '',
                'github_allowed_organizations': ''
            },
            'google': {
                'disabled': False,
                'client_id': '',
                'client_secret': ''
            },
            'bitbucket': {
                'disabled': True,
                'client_id': '',
                'client_secret': ''
            },
        }
        dirty = True
    if 'openid' not in data['authentication']:
        data['authentication']['openid'] = {
            'disabled': False,
            'server': 'https://login.launchpad.net/+openid',
            'login_button_text': 'Log in with the Launchpad service'
        }
        dirty = True
    if data['authentication'].get('github'):
        (data['authentication']['oauth2']
         ['github']['disabled']) = (data['authentication']['github']
                                    ['disabled'])
        (data['authentication']['oauth2']
         ['github']['client_id']) = (data['authentication']['github']
                                     ['github_app_id'])
        (data['authentication']['oauth2']
         ['github']['client_secret']) = (data['authentication']['github']
                                         ['github_app_secret'])
        (data['authentication']['oauth2']['github']
         ['github_allowed_organizations']) = (data['authentication']
                                              ['github']
                                              ['github_allowed_organizations'])
        if data['authentication']['github'].get('redirect_uri'):
            (data['authentication']['oauth2']['github']
             ['redirect_uri']) = string.replace(data['authentication']
                                                ['github']['redirect_uri'],
                                                "login/github/callback",
                                                "login/oauth2/callback")
        del data['authentication']['github']
        dirty = True
    if data['authentication'].get('launchpad'):
        (data['authentication']['openid']
         ['disabled']) = data['authentication']['launchpad']['disabled']
        if data['authentication']['launchpad'].get('redirect_uri'):
            (data['authentication']['openid']
             ['redirect_uri']) = (data['authentication']['launchpad']
                                  ['redirect_uri'])
        del data['authentication']['launchpad']
        dirty = True

    if 'gerrit_connections' not in data:
        data['gerrit_connections'] = []
        dirty = True

    if 'periodic_update' not in data['mirrors']:
        data['mirrors']['periodic_update'] = False
        dirty = True
    if 'swift_mirror_ttl' not in data['mirrors']:
        data['mirrors']['swift_mirror_ttl'] = 15811200
        dirty = True

    if 'use_letsencrypt' not in data['network']:
        data['network']['use_letsencrypt'] = False

    # Mumble is enable when the role is defined in arch
    if 'disabled' in data['mumble']:
        del data['mumble']['disabled']
        dirty = True

    # 2.2.5: finished arch aware top-menu, remove service toggle now
    for hideable in ('redmine', 'etherpad', 'paste'):
        key = 'topmenu_hide_%s' % hideable
        if key in data['theme']:
            del data['theme'][key]
            dirty = True

    # 2.2.6: enforce_ssl is enabled by default
    if 'enforce_ssl' in data['network']:
        del data['network']['enforce_ssl']
        dirty = True

    # 2.2.7: add openid_connect settings
    if 'openid_connect' not in data['authentication']:
        data['authentication']['openid_connect'] = {
            'disabled': True,
            'issuer_url': None,
            'client_secret': None,
            'client_id': None,
            'login_button_text': 'Log in with OpenID Connect'
        }
        dirty = True

    # 2.2.7 rename variables for jinja2 templates
    old_names = ["auth-url", "project-id", "max-servers", "boot-timeout"]
    for value in data['nodepool']['providers']:
        for name in old_names:
            if name in value:
                value[name.replace('-', '_')] = value.pop(name)
                dirty = True

    # 2.2.7: add oidc field mapping, default to google values
    if 'mapping' not in data['authentication']['openid_connect']:
        data['authentication']['openid_connect']['mapping'] = {
            'login': 'email',
            'email': 'email',
            'name': 'name',
            'uid': 'sub',
            'ssh_keys': None
        }

    # 2.3.0: enable static hosts settings
    if 'static_hostnames' not in data['network']:
        data['network']['static_hostnames'] = []
        dirty = True

    # 2.3.0: add debug setting
    if 'debug' not in data:
        data['debug'] = False
        dirty = True

    # 2.4.0: add welcome page setting
    if 'welcome_page_path' not in data:
        data['welcome_page_path'] = "sf/welcome.html"
        dirty = True

    return dirty


def clean_arch(data):
    dirty = False
    # Rename auth in cauth
    for host in data['inventory']:
        if 'auth' in host['roles']:
            host['roles'].remove('auth')
            host['roles'].append('cauth')
            dirty = True
    # Remove data added *IN-PLACE* by utils_refarch
    # Those are now saved in _arch.yaml instead
    for dynamic_key in ("domain", "gateway", "gateway_ip", "install",
                        "install_ip", "ip_prefix", "roles", "hosts_file"):
        if dynamic_key in data:
            del data[dynamic_key]
            dirty = True

    # Remove deployments related information
    for deploy_key in ("cpu", "disk", "mem", "hostid", "rolesname",
                       "hostname"):
        for host in data["inventory"]:
            if deploy_key in host:
                del host[deploy_key]
                dirty = True
    return dirty


if len(argv) == 2:
    hiera_dir = argv[1]
else:
    hiera_dir = "/etc/software-factory"

if not os.path.isdir(hiera_dir):
    print "usage: %s hiera_dir" % argv[0]
    exit(1)

# arch.yaml
try:
    arch = load("arch")
except IOError:
    # 2.1.x -> 2.2.x: arch is missing, force update
    arch = yaml.load(open(DEFAULT_ARCH).read())
    save("arch", arch)

if clean_arch(arch):
    save("arch", arch)

# sfconfig.yaml
sfconfig = load("sfconfig")
if update_sfconfig(sfconfig):
    save("sfconfig", sfconfig)
