"""Regression test for padded point records and organized cloud rows."""
import importlib.machinery
from array import array
from pathlib import Path
import struct
import unittest

from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import PointCloud2, PointField

fusion = importlib.machinery.SourceFileLoader(
    'cloud_fusion', str(Path(__file__).resolve().parents[1] / 'scripts' / 'fuse_point_clouds')
).load_module()


class CloudLayoutTest(unittest.TestCase):
    def test_transform_preserves_fields_and_padding(self):
        for endian, byte_order in ((False, '<'), (True, '>')):
            with self.subTest(big_endian=endian):
                fields = [PointField(name=name, offset=offset, datatype=datatype, count=1)
                          for name, offset, datatype in [('x', 0, 7), ('y', 4, 7),
                                                         ('z', 8, 7), ('rgb', 12, 6)]]
                row = struct.pack(byte_order + 'fffI4s', 1, 2, 3, 0x12345678, b'abcd') + b'row!'
                cloud = PointCloud2(height=2, width=1, fields=fields, is_bigendian=endian,
                                    point_step=20, row_step=24, data=array('B', row * 2))
                transform = TransformStamped()
                transform.transform.rotation.w = 1.0
                transform.transform.translation.x = 2.0
                result = fusion.transform_cloud_data(cloud, transform)
                self.assertEqual(len(result), 40)
                for offset in (0, 20):
                    self.assertEqual(struct.unpack_from(byte_order + 'fffI4s', result, offset),
                                     (3.0, 2.0, 3.0, 0x12345678, b'abcd'))


if __name__ == '__main__':
    unittest.main()
