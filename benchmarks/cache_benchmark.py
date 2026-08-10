import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from caching import benchmark_cache, cache


if __name__ == '__main__':
  cache.clear()

  def load_once():
    return {'value': 1}

  repeated = benchmark_cache(lambda: load_once(), iterations=1000)
  print(f'cache benchmark (1000 iterations): {repeated:.6f}s')
