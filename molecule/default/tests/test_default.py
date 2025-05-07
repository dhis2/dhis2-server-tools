"""DHIS2 deployment testing module."""
import pytest


def test_dhis2_packages(host):
    """Verify required packages are installed."""
    packages = [
        'openjdk-11-jdk',
        'nginx',
        'postgresql'
    ]
    
    for package in packages:
        pkg = host.package(package)
        assert pkg.is_installed


def test_dhis2_service(host):
    """Verify DHIS2 service is running and enabled."""
    service = host.service('dhis2')
    assert service.is_enabled
    assert service.is_running


def test_dhis2_ports(host):
    """Verify required ports are listening."""
    ports = [8080, 80, 443]
    
    for port in ports:
        assert host.socket(f"tcp://0.0.0.0:{port}").is_listening


@pytest.mark.parametrize('directory', [
    '/opt/dhis2',
    '/opt/dhis2/config',
    '/opt/dhis2/logs'
])
def test_dhis2_directories(host, directory):
    """Verify DHIS2 directories exist with correct permissions."""
    dir = host.file(directory)
    assert dir.exists
    assert dir.is_directory
    assert dir.user == 'dhis'
    assert dir.group == 'dhis'