"""CLI 主流程：argparse + 调用各模块的串接。"""
import unittest
from unittest.mock import patch
from simulator import cli
from simulator.shared.constants import TABLE_NAMES


class TestBootstrapCommand(unittest.TestCase):
    def test_runs_schemas_then_seeds_all_tables(self):
        with patch("simulator.cli.VikaClient"), \
             patch("simulator.cli.bootstrap_schemas") as mock_boot, \
             patch("simulator.cli.seed_table") as mock_seed:
            mock_boot.return_value = {name: f"dst_{key}"
                                       for key, name in TABLE_NAMES.items()}
            mock_seed.return_value = 100
            cli.main(["bootstrap"])

            mock_boot.assert_called_once()
            self.assertEqual(mock_seed.call_count, 7)

    def test_dry_run_passes_flag_through(self):
        with patch("simulator.cli.VikaClient"), \
             patch("simulator.cli.bootstrap_schemas") as mock_boot, \
             patch("simulator.cli.seed_table") as mock_seed:
            mock_boot.return_value = {name: f"dst_{key}"
                                       for key, name in TABLE_NAMES.items()}
            mock_seed.return_value = 0  # CLI uses {n:5d} format
            cli.main(["bootstrap", "--dry-run"])
            for call in mock_seed.call_args_list:
                self.assertTrue(call.kwargs.get("dry_run"))


if __name__ == "__main__":
    unittest.main()
