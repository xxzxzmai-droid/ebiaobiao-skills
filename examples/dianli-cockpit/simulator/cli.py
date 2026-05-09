"""dianli-cockpit Phase A CLI.

Subcommands:
  bootstrap [--dry-run] [--reseed] [--skip-existing] [--seed N]
      build schemas + seed data
"""
import argparse
import logging
import sys
from typing import List, Optional

from simulator.shared import generators
from simulator.shared.bootstrap import bootstrap_schemas
from simulator.shared.constants import TABLE_NAMES
from simulator.shared.schema import ALL_SCHEMAS
from simulator.shared.seeder import seed_table
from simulator.shared.vika import VikaClient


SEEDERS = [
    # (table_name, generator_func, key_fields)
    (TABLE_NAMES["industry"], generators.generate_industry_metrics,
     ["月份", "区域", "行业"]),
    (TABLE_NAMES["enterprise"], generators.generate_enterprises,
     ["企业名称", "日期"]),
    (TABLE_NAMES["load_curve"], generators.generate_load_curve,
     ["时间戳", "区域"]),
    (TABLE_NAMES["alert"], generators.generate_alerts,
     ["事件编号"]),
    (TABLE_NAMES["renewable"], generators.generate_renewable,
     ["日期", "区域"]),
    (TABLE_NAMES["insight"], generators.generate_insights,
     ["时间", "区域", "类型"]),
    (TABLE_NAMES["config"], generators.generate_config,
     ["参数"]),
]


def cmd_bootstrap(args, client: VikaClient):
    print("→ Phase A: 创建 / 复用 7 张数据表的 schema...")
    dst_ids = bootstrap_schemas(client, ALL_SCHEMAS)
    print(f"  ✓ {len(dst_ids)} 张表 schema 就位:")
    for name, dst in dst_ids.items():
        print(f"    {name:30} {dst}")

    print("\n→ 灌入种子数据 (幂等)...")
    total_new = 0
    for table_name, gen_func, key_fields in SEEDERS:
        gen_args = {"seed": args.seed} \
                   if "seed" in gen_func.__code__.co_varnames else {}
        records = gen_func(**gen_args)
        n = seed_table(client, dst_ids[table_name], records,
                       key_fields=key_fields, dry_run=args.dry_run)
        total_new += n
        print(f"  {table_name:30} 新增 {n:5d} / 共生成 {len(records):5d}")

    prefix = "(dry-run) " if args.dry_run else ""
    print(f"\n{prefix}总计新增 {total_new} 条记录")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="simulator",
        description="dianli-cockpit Phase A CLI",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    bs = sub.add_parser("bootstrap", help="create schemas + seed data")
    bs.add_argument("--dry-run", action="store_true",
                    help="print actions without writing")
    bs.add_argument("--reseed", action="store_true",
                    help="(reserved) wipe records before seed")
    bs.add_argument("--skip-existing", action="store_true",
                    help="skip records whose key already exists (default behavior)")
    bs.add_argument("--seed", type=int, default=1,
                    help="random seed (default 1)")

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(message)s")

    client = VikaClient()
    if args.cmd == "bootstrap":
        cmd_bootstrap(args, client)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
