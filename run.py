#!/usr/bin/env python
"""
Athome Property Scraper - シンプル実行スクリプト
Windowsとの互換性を重視したバージョン
"""
import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from scripts import run_scraper

if __name__ == "__main__":
    run_scraper.main()