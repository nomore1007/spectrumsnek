"""Unit tests for exclusive SDR ownership; no RTL-SDR hardware required."""
import os
import tempfile
import unittest

from sdr_manager import SDRBusyError, SDRManager


class SDRManagerTests(unittest.TestCase):
    def test_only_one_manager_can_own_device(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = os.path.join(tmp, "sdr.lock")
            first = SDRManager(lock_path=lock)
            second = SDRManager(lock_path=lock)
            first.acquire_device("test-first")
            try:
                with self.assertRaises(SDRBusyError):
                    second.acquire_device("test-second")
            finally:
                first.release_device()
            second.acquire_device("test-second")
            second.release_device()

    def test_release_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = SDRManager(lock_path=os.path.join(tmp, "sdr.lock"))
            manager.release_device()
            manager.acquire_device("test")
            manager.release_device()
            manager.release_device()


if __name__ == "__main__":
    unittest.main()
