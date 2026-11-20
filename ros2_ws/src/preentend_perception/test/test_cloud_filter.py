"""Tests for ground and robot collision geometry filtering."""
import importlib.machinery
from pathlib import Path
import unittest

import numpy as np
from scipy.spatial.transform import Rotation

filter_node = importlib.machinery.SourceFileLoader(
    'cloud_filter', str(Path(__file__).resolve().parents[1] / 'scripts' / 'filter_point_cloud')
).load_module()


class RobotMaskTest(unittest.TestCase):
    def test_translated_rotated_box_and_ground(self):
        urdf = '''<robot name="test"><link name="arm"><collision>
          <origin xyz="1 0 0"/><geometry><box size="2 0.5 1"/></geometry>
        </collision></link></robot>'''
        shapes = filter_node.collision_shapes(urdf, 0.04)
        transforms = {'arm': (np.array([0., 0., 1.]), Rotation.from_euler('z', 90, degrees=True))}
        points = np.array([[0., 1., 1.], [1., 1., 1.], [0., 0., 0.]])
        candidates = np.flatnonzero(points[:, 2] > 0.03)
        kept = candidates[~filter_node.robot_mask(points[candidates], shapes, transforms, 0.05)]
        self.assertEqual(kept.tolist(), [1])

    def test_sampled_mesh_surface(self):
        triangles = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]])
        samples = filter_node.sample_mesh(triangles, 0.04)
        tree = filter_node.cKDTree(samples)
        shape = ('arm', np.zeros(3), Rotation.identity(),
                 ('mesh', tree, samples.min(axis=0), samples.max(axis=0)))
        points = np.array([[0.3, 0.3, 0.02], [0.3, 0.3, 0.2]])
        self.assertEqual(filter_node.robot_mask(points, [shape],
                         {'arm': (np.zeros(3), Rotation.identity())}, 0.05).tolist(), [True, False])


if __name__ == '__main__':
    unittest.main()
