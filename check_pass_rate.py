#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def check_allure_pass_rate(min_pass_rate: float):
    """检查Allure报告通过率"""
    results_dir = Path("report")

    if not results_dir.exists():
        print(f"错误：Allure结果目录不存在 {results_dir}")
        return False

    # 解析Allure结果文件
    passed = 0
    total = 0

    for result_file in results_dir.glob("*.json"):
        with open(result_file, encoding="utf-8") as f:
            try:
                data = json.load(f)
                if data["status"] in ("passed", "failed", "broken"):
                    total += 1
                    if data["status"] == "passed":
                        passed += 1
            except (json.JSONDecodeError, KeyError) as e:
                print(f"警告：解析文件 {result_file} 出错: {e}")

    if total == 0:
        print("错误：未找到有效的测试结果")
        return False

    pass_rate = (passed / total) * 100
    print(f"测试通过率: {pass_rate:.2f}% ({passed}/{total})")

    if pass_rate < min_pass_rate:
        print(f"❌ 通过率低于最低要求 {min_pass_rate}%")
        return False

    print(f"✅ 通过率达标 (≥ {min_pass_rate}%)")
    return True


if __name__ == "__main__":
    try:
        min_rate = float(sys.argv[1]) if len(sys.argv) > 1 else 90.0
        success = check_allure_pass_rate(min_rate)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"执行出错: {e}")
        sys.exit(1)