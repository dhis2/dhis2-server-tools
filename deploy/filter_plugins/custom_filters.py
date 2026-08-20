import ipaddress
import re
from urllib.parse import urlparse
from netaddr import IPAddress, IPNetwork
from ansible.module_utils.compat.version import LooseVersion
from ansible.module_utils.common.text.converters import to_text
from ansible.errors import (
    # AnsibleError,
    AnsibleFilterError,
    # AnsibleFilterTypeError
)


# ensures dhis2_version is correct e.g 2.42 and not 2.43.b
def normalize_dhis2_version(dhis2_version, dhis2_releases):
    version_list = [item['name'] for item in dhis2_releases]
    pattern = r'^\d+(\.\d+)*$'
    if isinstance(dhis2_version, float):
        dhis2_version_major = str(format(dhis2_version, '.2f'))
        if dhis2_version_major in version_list:
            return {'dhis2_version_major': dhis2_version_major,
                    'dhis2_version_minor': None
                    }
        else:
            raise AnsibleFilterError(f"The version {dhis2_version} is not in "
                                     f"released versions, '{version_list}'"
                                     )
    elif isinstance(dhis2_version, str):
        if re.match(pattern, dhis2_version):
            dhis2_version_major = ('.'.join(dhis2_version.split('.')[:2]))
            dhis2_version_minor = dhis2_version
            if dhis2_version_major in version_list:
                return {'dhis2_version_major': dhis2_version_major,
                        'dhis2_version_minor': dhis2_version_minor
                        }
            else:
                raise AnsibleFilterError(f"The version {dhis2_version} is not "
                                         f"in released versions, '{version_list}'"
                                         )
        else:
            raise AnsibleFilterError(f"The version '{dhis2_version}' is not in a valid format. "
                                     f"Expected format: 2.major[.minor][.patch]"
                                     )


# precise_version
# preserve_version_precision
def to_fixed_string(value):
    if isinstance(value, float):
        # Adjust the precision (number of decimal places) as needed
        return format(value, '.2f')  # Ensures e.g., 2.0 → "2.00", 2.3 → "2.30"
    return str(value)


# get_dhis2_instance_specs
def get_dhis2_instance_specs(dhis2_version, dhis2_auto_upgrade, version_results):
    ''' Determine java_version based on dhis2_version variable '''
    Version = LooseVersion
    version_stdout = version_results.get('stdout', '') if version_results else ''
    version_skipped = not version_stdout or 'skipped' in version_stdout
    version_actual = dhis2_version if version_skipped else '.'.join(version_stdout.split('.')[:2])

    def str_to_bool(value):
        """
        Convert a string representation of truth to True or False.

        True values are 'yes', 'true', 't', '1', 'y'
        False values are 'no', 'false', 'f', '0', 'n'
        """
        if isinstance(value, str):
            value = value.strip().lower()
            if value in ('yes', 'true', 't', '1', 'y'):
                return True
            elif value in ('no', 'false', 'f', '0', 'n'):
                return False
        return bool(value)

    # exact version matching
    def version_eq(version1, version2):
        return Version(to_text(version1)) == Version(to_text(version2))

    def version_gte(version1, version2):
        return Version(to_text(version1)) >= Version(to_text(version2))

    def version_lte(version1, version2):
        return Version(to_text(version2)) >= Version(to_text(version1))

    if (version_gte(version_actual, '2.42') or (version_gte(dhis2_version, '2.42') and str_to_bool(dhis2_auto_upgrade))):
        return {'jdk': 17,
                'tomcat': 10,
                'javax_jakartaee_convert': False,
                'guest_os': ['24.04'],
                }

    if (version_eq(version_actual[:4], '2.41') or (version_eq(dhis2_version, '2.41') and str_to_bool(dhis2_auto_upgrade))):
        return {'jdk': 17,
                'tomcat': 9,
                'guest_os': ['22.04', '24.04']
                }

    if (version_gte(version_actual, '2.35') and version_lte(version_actual, '2.40')):
        return {'jdk': 11,
                'tomcat': 9,
                'guest_os': ['22.04', '24.04'],
                }

    return {'jdk': 8,
            'tomcat': 9,
            'guest_os': ['22.04', '24.04']
            }


def all_have_fqdn(instances, hostvars):
    """Check if all instances have a valid (non-empty) fqdn defined."""
    for instance in instances:
        fqdn = hostvars.get(instance, {}).get('fqdn', '')
        if not (fqdn and str(fqdn).strip()):
            return False
    return True


def lowercase(value):
    if isinstance(value, str):
        if value is not None and value != 'None':
            return str(value).lower()
    else:
        return value  # Return the value unchanged if it's not a string


def tomcat_version(distribution_version):
    if distribution_version == '24.04':
        return 10
    else:
        return 9


def external_hosts(hosts, hostvars, lxd_network):
    """Return hosts whose ansible_host is not in lxd_network."""
    network = IPNetwork(lxd_network)
    result = []
    for h in hosts:
        if h == '127.0.0.1':
            continue
        ansible_host = hostvars.get(h, {}).get('ansible_host')
        if ansible_host and IPAddress(ansible_host) not in network:
            result.append(h)
    return result


_LOOPBACK_NAMES = frozenset({
    'localhost',
    'ip6-localhost',
    'ip6-loopback',
    'localhost.localdomain',
})


def _clean_conf_value(value, name):
    text = '' if value is None else str(value)
    if any(ord(c) < 32 or ord(c) == 127 for c in text):
        raise AnsibleFilterError(
            f"{name} must not contain control characters"
        )
    if any(c.isspace() for c in text.strip()):
        raise AnsibleFilterError(
            f"{name} must not contain whitespace"
        )
    return text.strip()


def _host_ip(name):
    try:
        return ipaddress.ip_address(name)
    except ValueError:
        parts = name.split('.')
        if not (2 <= len(parts) <= 3 and all(p.isdigit() for p in parts)):
            return None
        padded = parts[:-1] + ['0'] * (4 - len(parts)) + parts[-1:]
        try:
            return ipaddress.IPv4Address('.'.join(padded))
        except ValueError:
            return None


def _is_blocked_host(host):
    if not host:
        return True
    name = host.strip('[]').lower()
    if name in _LOOPBACK_NAMES:
        return True
    ip = _host_ip(name)
    return ip is not None and (ip.is_loopback or ip.is_unspecified)


def _canonical_https_url(url, source):
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError as exc:
        raise AnsibleFilterError(
            f"{source} is not a valid https URL"
        ) from exc
    if parsed.scheme != 'https':
        raise AnsibleFilterError(
            f"{source} must be an https URL"
        )
    if parsed.username is not None or parsed.password is not None:
        raise AnsibleFilterError(
            f"{source} must not contain userinfo"
        )
    if parsed.query or parsed.fragment:
        raise AnsibleFilterError(
            f"{source} must not contain a query string or fragment"
        )
    host = parsed.hostname
    if host is None or _is_blocked_host(host):
        raise AnsibleFilterError(
            f"{source} hostname must be reachable by end users, not localhost"
        )
    path = parsed.path.rstrip('/')
    if '//' in path or any(seg in ('.', '..') for seg in path.split('/')):
        raise AnsibleFilterError(
            f"{source} path is not a valid DHIS2 context path"
        )
    if ':' in host:
        try:
            ipaddress.IPv6Address(host)
        except ValueError as exc:
            raise AnsibleFilterError(
                f"{source} hostname is not a valid IPv6 address"
            ) from exc
        netloc = f'[{host}]'
    else:
        netloc = host
    if port is not None and port != 443:
        netloc = f'{netloc}:{port}'
    return f'https://{netloc}{path}'


def dhis2_server_base_url(override, fqdn='', context='', https_port=443):
    """Public URL for dhis.conf server.base.url, or '' when it must be omitted."""
    override = _clean_conf_value(override, 'server_base_url')
    if override:
        return _canonical_https_url(override.rstrip('/'), 'server_base_url')

    fqdn = _clean_conf_value(fqdn, 'fqdn')
    if not fqdn:
        return ''
    if '/' in fqdn or '@' in fqdn or '://' in fqdn or ':' in fqdn:
        raise AnsibleFilterError('fqdn must be a hostname, not a URL')

    try:
        port = int(https_port)
    except (TypeError, ValueError) as exc:
        raise AnsibleFilterError(
            f"https_port must be an integer, got {https_port!r}"
        ) from exc
    if port < 1 or port > 65535:
        raise AnsibleFilterError(f"https_port must be 1-65535, got {port}")

    raw_context = 'ROOT' if context in (None, '') else context
    context_s = _clean_conf_value(to_fixed_string(raw_context), 'dhis2_base_path')
    if context_s != 'ROOT' and (
            context_s.startswith('/') or '/' in context_s
            or context_s in ('.', '..')):
        raise AnsibleFilterError(
            'dhis2_base_path must be a single path segment or ROOT'
        )

    netloc = fqdn if port == 443 else f'{fqdn}:{port}'
    path = '' if context_s == 'ROOT' else f'/{context_s}'
    return _canonical_https_url(f'https://{netloc}{path}', 'fqdn')


class FilterModule(object):
    def filters(self):
        return {'get_dhis2_instance_specs': get_dhis2_instance_specs,
                'external_hosts': external_hosts,
                'to_fixed_string': to_fixed_string,
                'lowercase': lowercase,
                'tomcat_version': tomcat_version,
                'normalize_dhis2_version': normalize_dhis2_version,
                'all_have_fqdn': all_have_fqdn,
                'dhis2_server_base_url': dhis2_server_base_url,
                }
