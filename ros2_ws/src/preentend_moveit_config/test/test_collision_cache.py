"""Regression tests for collision cache invalidation and failure handling."""

from concurrent.futures import ThreadPoolExecutor
import subprocess
from unittest.mock import patch
import xml.etree.ElementTree as ET

import pytest

from preentend_moveit_config.collision_cache import get_collision_srdf


@pytest.fixture
def setup_cache(tmp_path):
    mesh = tmp_path / 'arm.stl'
    mesh.write_bytes(b'original collision mesh')
    updater = tmp_path / 'lib/moveit_setup_assistant/collisions_updater'
    updater.parent.mkdir(parents=True)
    updater.write_bytes(b'collision updater')
    robot = ET.Element('robot', name='preentend')
    for prefix in ('robot_1_', 'robot_2_'):
        for name in ('base_link', *(f'link_{i}' for i in range(1, 7))):
            link = ET.SubElement(robot, 'link', name=prefix + name)
            collision = ET.SubElement(link, 'collision')
            geometry = ET.SubElement(collision, 'geometry')
            ET.SubElement(geometry, 'mesh', filename=mesh.as_uri())
    urdf = ET.tostring(robot, encoding='unicode')
    srdf = '<robot name="preentend"><group name="robots"/></robot>'
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        groups = ET.parse(command[command.index('--srdf') + 1]).getroot()
        ET.SubElement(groups, 'disable_collisions', link1='robot_1_base_link',
                      link2='robot_2_base_link', reason='Never')
        ET.ElementTree(groups).write(command[command.index('--output') + 1], encoding='unicode')
        return subprocess.CompletedProcess(command, 0, '', '')

    with patch('preentend_moveit_config.collision_cache.get_package_prefix', return_value=str(tmp_path)), \
         patch('preentend_moveit_config.collision_cache.subprocess.run', side_effect=run):
        yield tmp_path, mesh, urdf, srdf, calls


def test_cache_hits_and_invalidates_for_arguments_geometry_and_trials(setup_cache):
    directory, mesh, urdf, srdf, calls = setup_cache
    cache = directory / 'cache'
    args = {'robot_model': 'kr30_r2100', 'separation': '4.0'}
    first, hit = get_collision_srdf(urdf, srdf, args, 1000, cache)
    assert not hit
    assert get_collision_srdf(urdf, srdf, args, 1000, cache) == (first, True)
    assert len(calls) == 1
    assert not get_collision_srdf(urdf, srdf, dict(args, separation='3.0'), 1000, cache)[1]
    assert not get_collision_srdf(urdf, srdf, args, 1001, cache)[1]
    assert not get_collision_srdf(urdf, srdf.replace('robots', 'robot_1'), args, 1000, cache)[1]
    changed_urdf = urdf.replace('</robot>', '<link name="extra"/></robot>')
    assert not get_collision_srdf(changed_urdf, srdf, args, 1000, cache)[1]
    (directory / 'lib/moveit_setup_assistant/collisions_updater').write_bytes(b'updated updater')
    assert not get_collision_srdf(urdf, srdf, args, 1000, cache)[1]
    mesh.write_bytes(b'changed collision mesh')
    assert not get_collision_srdf(urdf, srdf, args, 1000, cache)[1]
    assert len(calls) == 7


def test_invalid_cache_is_regenerated_and_missing_mesh_is_rejected(setup_cache):
    directory, mesh, urdf, srdf, calls = setup_cache
    cache = directory / 'cache'
    args = {'robot_model': 'kr30_r2100'}
    get_collision_srdf(urdf, srdf, args, 1000, cache)
    next(cache.glob('*.srdf')).write_text('<bad>')
    assert not get_collision_srdf(urdf, srdf, args, 1000, cache)[1]
    assert len(calls) == 2
    mesh.unlink()
    with pytest.raises(FileNotFoundError):
        get_collision_srdf(urdf, srdf, args, 1000, cache)
    assert len(calls) == 2


def test_simultaneous_requests_generate_only_once(setup_cache):
    directory, _, urdf, srdf, calls = setup_cache
    args = {'robot_model': 'kr30_r2100'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(get_collision_srdf, urdf, srdf, args, 1000,
                               directory / 'cache') for _ in range(2)]
        results = [future.result() for future in futures]
    assert sorted(hit for _, hit in results) == [False, True]
    assert results[0][0] == results[1][0]
    assert len(calls) == 1


def test_failed_generation_is_not_cached(setup_cache):
    directory, _, urdf, srdf, _ = setup_cache
    args = {'robot_model': 'kr30_r2100'}
    failure = subprocess.CalledProcessError(1, ['collisions_updater'], stderr='bad geometry')
    with patch('preentend_moveit_config.collision_cache.subprocess.run', side_effect=failure):
        with pytest.raises(RuntimeError, match='bad geometry'):
            get_collision_srdf(urdf, srdf, args, 1000, directory / 'cache')
    assert not list((directory / 'cache').glob('*.srdf'))
    assert not get_collision_srdf(urdf, srdf, args, 1000, directory / 'cache')[1]
