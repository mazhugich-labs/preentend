"""Generate and cache a self-collision SRDF for a complete robot description."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_prefix, get_package_share_directory


CACHE_VERSION = 'preentend-collision-cache-v1'


def _collision_meshes(robot):
    """Resolve every collision mesh; a missing mesh must not yield a matrix."""
    meshes = set()
    for prefix in ('robot_1_', 'robot_2_'):
        for name in ('base_link', *(f'link_{i}' for i in range(1, 7))):
            if robot.find(f"link[@name='{prefix}{name}']/collision") is None:
                raise ValueError(f'{prefix}{name} has no collision geometry')
    for mesh in robot.findall('./link/collision/geometry/mesh'):
        uri = mesh.get('filename', '')
        if uri.startswith('package://'):
            package, relative = uri[len('package://'):].split('/', 1)
            path = Path(get_package_share_directory(package)) / relative
        elif uri.startswith('file://'):
            parsed = urlparse(uri)
            if parsed.netloc not in ('', 'localhost'):
                raise ValueError(f'Unsupported collision mesh URI: {uri}')
            path = Path(unquote(parsed.path))
        elif Path(uri).is_absolute():
            path = Path(uri)
        else:
            raise ValueError(f'Unsupported collision mesh URI: {uri}')
        if not path.is_file():
            raise FileNotFoundError(f'Collision mesh not found: {path}')
        meshes.add((uri, path))
    return sorted(meshes, key=lambda entry: entry[0])


def _hash_file(digest, path):
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(block)


def _valid_srdf(text, robot, groups):
    try:
        root = ET.fromstring(text)
        links = {link.get('name') for link in robot.findall('link')}
        expected_groups = {group.get('name') for group in groups.findall('group')}
        return (root.tag == 'robot' and root.get('name') == robot.get('name')
                and {group.get('name') for group in root.findall('group')} == expected_groups
                and bool(root.findall('disable_collisions'))
                and all(rule.get('link1') in links and rule.get('link2') in links
                        for rule in root.findall('disable_collisions')))
    except ET.ParseError:
        return False


def get_collision_srdf(robot_description, semantic_template, mappings, trials, cache_dir):
    """Return (SRDF, cache_hit), recomputing for changed arguments or geometry."""
    if trials < 1:
        raise ValueError('collision_trials must be positive')
    robot = ET.fromstring(robot_description)
    groups = ET.fromstring(semantic_template)
    for rule in list(groups.findall('disable_collisions')):
        groups.remove(rule)
    if groups.get('name') != robot.get('name') or not groups.findall('group'):
        raise ValueError('Robot and semantic descriptions do not contain matching planning groups')
    group_xml = ET.tostring(groups, encoding='unicode')
    updater = Path(get_package_prefix('moveit_setup_assistant')) / 'lib/moveit_setup_assistant/collisions_updater'
    if not updater.is_file():
        raise FileNotFoundError(f'MoveIt collisions_updater not found: {updater}')

    digest = hashlib.sha256()
    for value in (CACHE_VERSION, robot_description, group_xml,
                  json.dumps(mappings, sort_keys=True, separators=(',', ':')), str(trials)):
        digest.update(value.encode('utf-8'))
        digest.update(b'\0')
    _hash_file(digest, updater)
    for uri, path in _collision_meshes(robot):
        digest.update(uri.encode('utf-8'))
        digest.update(b'\0')
        _hash_file(digest, path)
    cache_dir = Path(cache_dir).expanduser()
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = digest.hexdigest()
    cache_file = cache_dir / f'{key}.srdf'
    with (cache_dir / f'{key}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if cache_file.is_file():
            cached = cache_file.read_text(encoding='utf-8')
            if _valid_srdf(cached, robot, groups):
                return cached, True
        with tempfile.TemporaryDirectory(prefix='.collision-', dir=cache_dir) as directory:
            directory = Path(directory)
            urdf_file, groups_file, output_file = (
                directory / 'robot.urdf', directory / 'groups.srdf', directory / 'result.srdf'
            )
            urdf_file.write_text(robot_description, encoding='utf-8')
            groups_file.write_text(group_xml, encoding='utf-8')
            try:
                result = subprocess.run(
                    [str(updater), '--urdf', str(urdf_file), '--srdf', str(groups_file),
                     '--output', str(output_file), '--trials', str(trials)],
                    check=True, capture_output=True, text=True,
                )
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    'Collision matrix generation failed:\n' + (exc.stdout or '') + (exc.stderr or '')
                ) from exc
            if '[ERROR]' in result.stdout or '[ERROR]' in result.stderr:
                raise RuntimeError('Collision matrix generation failed:\n' + result.stdout + result.stderr)
            srdf = output_file.read_text(encoding='utf-8')
            if not _valid_srdf(srdf, robot, groups):
                raise ValueError('Generated collision SRDF does not match the robot description')
            os.replace(output_file, cache_file)
            return srdf, False
