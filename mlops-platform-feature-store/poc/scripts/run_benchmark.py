"""
Feast Online Store Benchmark: Redis vs ScyllaDB
- Generate sample data
- feast apply + materialize for both stores
- Measure get_online_features() latency (p50/p95/p99)
"""
import os
import time
import json
import shutil
import subprocess
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from cassandra.cluster import Cluster

DATA_DIR = "/data"
RESULTS_DIR = "/results"
PARQUET_PATH = f"{DATA_DIR}/user_features.parquet"
NUM_ENTITIES = 1000
NUM_BENCHMARK_QUERIES = 500
ENTITIES_PER_QUERY = 10


def create_scylladb_keyspace():
    """Create the keyspace in ScyllaDB if it doesn't exist."""
    host = os.environ.get("SCYLLADB_HOST", "scylladb")
    print(f"[0/5] Creating ScyllaDB keyspace 'feast_online_dev' on {host}...")
    cluster = Cluster([host], port=9042, protocol_version=4)
    session = cluster.connect()
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS feast_online_dev
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
    """)
    session.shutdown()
    cluster.shutdown()
    print("    Keyspace created.")


def generate_data():
    """Generate sample feature data as parquet."""
    print(f"[1/5] Generating {NUM_ENTITIES} entity rows...")
    now = datetime.utcnow()
    df = pd.DataFrame({
        "user_id": [f"user_{i}" for i in range(NUM_ENTITIES)],
        "f_total_events_7d": np.random.randint(1, 500, NUM_ENTITIES),
        "f_avg_session_sec_7d": np.random.uniform(10.0, 3600.0, NUM_ENTITIES),
        "f_last_event_age_sec": np.random.randint(0, 604800, NUM_ENTITIES),
        "event_timestamp": [now - timedelta(hours=np.random.randint(1, 48))
                           for _ in range(NUM_ENTITIES)],
        "created": [now] * NUM_ENTITIES,
    })
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_parquet(PARQUET_PATH, index=False)
    print(f"    Saved to {PARQUET_PATH} ({len(df)} rows)")
    return df


def feast_apply_and_materialize(repo_path: str, store_name: str):
    """Run feast apply + materialize in the given repo directory."""
    print(f"[*] feast apply ({store_name})...")
    subprocess.run(["feast", "apply"], cwd=repo_path, check=True)

    end_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    start_ts = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
    print(f"[*] feast materialize ({store_name}): {start_ts} -> {end_ts}")
    subprocess.run(
        ["feast", "materialize", start_ts, end_ts],
        cwd=repo_path,
        check=True,
    )
    print(f"    Materialize complete ({store_name})")


def benchmark_online_store(repo_path: str, store_name: str) -> dict:
    """Benchmark get_online_features() latency."""
    from feast import FeatureStore

    print(f"[*] Benchmarking {store_name} ({NUM_BENCHMARK_QUERIES} queries, "
          f"{ENTITIES_PER_QUERY} entities/query)...")

    store = FeatureStore(repo_path=repo_path)

    # Warmup
    for _ in range(10):
        entity_ids = [f"user_{i}" for i in np.random.choice(NUM_ENTITIES, ENTITIES_PER_QUERY, replace=False)]
        store.get_online_features(
            features=["user_features:f_total_events_7d",
                       "user_features:f_avg_session_sec_7d",
                       "user_features:f_last_event_age_sec"],
            entity_rows=[{"user_id": uid} for uid in entity_ids],
        )

    # Benchmark
    latencies = []
    for i in range(NUM_BENCHMARK_QUERIES):
        entity_ids = [f"user_{i}" for i in np.random.choice(NUM_ENTITIES, ENTITIES_PER_QUERY, replace=False)]
        t0 = time.perf_counter()
        result = store.get_online_features(
            features=["user_features:f_total_events_7d",
                       "user_features:f_avg_session_sec_7d",
                       "user_features:f_last_event_age_sec"],
            entity_rows=[{"user_id": uid} for uid in entity_ids],
        )
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)  # ms

        # Verify data returned
        if i == 0:
            df = result.to_df()
            non_null = df["f_total_events_7d"].notna().sum()
            print(f"    First query: {len(df)} rows, {non_null} non-null features")

    latencies = np.array(latencies)
    stats = {
        "store": store_name,
        "queries": NUM_BENCHMARK_QUERIES,
        "entities_per_query": ENTITIES_PER_QUERY,
        "p50_ms": round(float(np.percentile(latencies, 50)), 2),
        "p95_ms": round(float(np.percentile(latencies, 95)), 2),
        "p99_ms": round(float(np.percentile(latencies, 99)), 2),
        "mean_ms": round(float(np.mean(latencies)), 2),
        "min_ms": round(float(np.min(latencies)), 2),
        "max_ms": round(float(np.max(latencies)), 2),
    }
    print(f"    {store_name}: p50={stats['p50_ms']}ms  p95={stats['p95_ms']}ms  "
          f"p99={stats['p99_ms']}ms  mean={stats['mean_ms']}ms")
    return stats


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # Step 0: Create ScyllaDB keyspace
    create_scylladb_keyspace()

    # Step 1: Generate data
    generate_data()

    results = {}

    # Step 2: Redis benchmark
    print("\n" + "=" * 60)
    print("[2/5] Redis: apply + materialize")
    print("=" * 60)
    redis_repo = "/feast-repo-redis"
    feast_apply_and_materialize(redis_repo, "Redis")

    print("\n[3/5] Redis: benchmark")
    results["redis"] = benchmark_online_store(redis_repo, "Redis")

    # Step 3: ScyllaDB benchmark
    print("\n" + "=" * 60)
    print("[4/5] ScyllaDB: apply + materialize")
    print("=" * 60)
    scylladb_repo = "/feast-repo-scylladb"
    feast_apply_and_materialize(scylladb_repo, "ScyllaDB")

    print("\n[5/5] ScyllaDB: benchmark")
    results["scylladb"] = benchmark_online_store(scylladb_repo, "ScyllaDB")

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Metric':<20} {'Redis':>12} {'ScyllaDB':>12}")
    print("-" * 44)
    for metric in ["p50_ms", "p95_ms", "p99_ms", "mean_ms"]:
        label = metric.replace("_ms", "").upper()
        r = results["redis"][metric]
        s = results["scylladb"][metric]
        print(f"{label:<20} {r:>10.2f}ms {s:>10.2f}ms")
    print("=" * 60)

    # Save results
    results_path = f"{RESULTS_DIR}/benchmark_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    main()
