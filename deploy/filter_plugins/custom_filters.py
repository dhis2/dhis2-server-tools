import re
from ansible.module_utils.compat.version import LooseVersion
from ansible.module_utils.common.text.converters import to_text
from ansible.errors import (
    # AnsibleError,
    AnsibleFilterError,
    # AnsibleFilterTypeError
)


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
            raise AnsibleFilterError(f"The version {dhis2_version} is not in"
                                     f"released versions, '{version_list}'"
                                     )
    elif isinstance(dhis2_version, str):
        if re.match(pattern, dhis2_version):
            dhis2_version_major = ('.'.join(dhis2_version.split('.')[:2]))
            dhis2_version_minor = dhis2_version
            if dhis2_version_major in version_list:
                return {
                      'dhis2_version_major': dhis2_version_major,
                      'dhis2_version_minor': dhis2_version_minor
                        }
            else:
                raise AnsibleFilterError(
                        f"The version {dhis2_version} is not"
                        f"in released versions, '{version_list}'"
                        )
        else:
            raise AnsibleFilterError(
                    f"The version '{dhis2_version}' is not in a valid format."
                    "Expected format: 2.major[.minor][.patch]"
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


class FilterModule(object):
    def filters(self):
        return {'get_dhis2_instance_specs': get_dhis2_instance_specs,
                'to_fixed_string': to_fixed_string,
                'lowercase': lowercase,
                'tomcat_version': tomcat_version,
                'normalize_dhis2_version': normalize_dhis2_version,
                }
