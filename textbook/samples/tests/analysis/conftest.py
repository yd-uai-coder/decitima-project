# DeciTima samples │ 作業単位 15-1 追補(ユーザー写経で発覚)
"""tests/analysis/ 配下の全テストに `analysis` マーカーを自動付与する。

analysis 依存群(pandas/matplotlib)は Docker イメージに意図的に含めていない(README §8
「NumPy/SciPy/pandas はコア層に入れない」)。個々の8テストファイルを手で
`@pytest.mark.analysis` デコレートする代わりに、ディレクトリ単位でこのフックが一括タグ付け
する ── `pyproject.toml` の `addopts`(`not analysis`)と組み合わせ、analysis グループが
入っていない環境(Docker コンテナ・CI ランナーの素の状態)でも bare `uv run pytest` が
collection エラーを起こさず常に通るようにする(`performance`/`integration` と同型)。
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: Sequence[pytest.Item]) -> None:
    # 写経の罠: pytest_collection_modifyitems は「歴史的フック」── conftest.py の
    # 置き場所に関わらず、収集された items 全件(他ディレクトリ含む)を毎回受け取る。
    # ディレクトリ配下だけに絞るには、自分で item.path が tests/analysis/ 配下かを判定する
    # 必要がある(フィクスチャのようなディレクトリスコープの自動絞り込みは無い)。
    for item in items:
        if _THIS_DIR in item.path.parents:
            item.add_marker(pytest.mark.analysis)
