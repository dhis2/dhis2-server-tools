from ansible.module_utils.compat.version import LooseVersion
from ansible.module_utils.common.text.converters import to_text

def to_fixed_string(value):
    if isinstance(value, float):
        return format(value, '.2f')  # Adjust the precision (number of decimal places) as needed
    return str(value)   

def determine_java_version(dhis2_version, dhis2_auto_upgrade, version_results):
    ''' Determine java_version based on dhis2_version '''

    Version = LooseVersion 
    version_stdout = version_results.get('stdout', '') if version_results else ''
    dhis2_version = to_fixed_string(dhis2_version)

    if isinstance(dhis2_version, float):
          dhis2_version = format(dhis2_version, '.2f')  # Adjust the precision (number of decimal places) as needed
    dhis2_version = str(dhis2_version)    

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

    def version_gte(version1, version2):
        return Version(to_text(version1)) >= Version(to_text(version2))

    def version_lte(version1, version2):
        return Version(to_text(version2)) >= Version(to_text(version1))

    if ('skipped' in version_stdout and version_gte(dhis2_version, 2.41)) or ('skipped' not in version_stdout and  version_gte(version_stdout,2.41)) or (version_gte(dhis2_version,2.41) and str_to_bool(dhis2_auto_upgrade)): 
        return 17
    elif ('skipped' in version_stdout and version_gte(dhis2_version, '2.35') and version_lte(dhis2_version,2.41))  or  ('skipped' not in version_stdout and version_gte(version_stdout, 2.35) and version_lte(version_stdout, 2.41)) or (version_gte(dhis2_version, 2.35) and version_lte(dhis2_version, 2.41) and str_to_bool(dhis2_auto_upgrade)):
        return 11
    else:
        return 8

def lowercase(value):
    if value is not None and value != 'None':
        return str(value).lower()
    return value

def tomcat_version(distribution_version):
    if distribution_version == '20.04' or distribution_version == '22.04':
        return  9
    else:
        return 10

def postgis_version(distribution_version):
    if distribution_version == '20.04':
        return 2.5
    else:
        return 3

class FilterModule(object):
    def filters(self):
        return {
            'determine_java_version': determine_java_version,
            'to_fixed_string': to_fixed_string,
            'lowercase': lowercase,
            'postgis_version': postgis_version,
            'tomcat_version': tomcat_version,
            }
