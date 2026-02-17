#!/usr/bin/env python3
"""
Test script for parallel processing implementation.
Run this to verify multiprocessing is working correctly.
"""

import time
from nlp_create_submission import generate_submission, generate_submission_parallel

# Test configuration - just a few chapters
test_config = [
    ([0, 1, 2], "paf", "data/prelude_a_fondation"),
    ([0, 1, 2], "lca", "data/les_cavernes_d_acier"),
]

anti_dict_file = "antidict.txt"
distance_max = 100

print("="*60)
print("TESTING PARALLEL vs SEQUENTIAL PROCESSING")
print("="*60)
print(f"Testing with 6 chapters (3 from each book)")
print()

# Test sequential
print("1️⃣  Running SEQUENTIAL processing...")
start_sequential = time.time()
df_seq = generate_submission(
    books_config=test_config,
    anti_dict_file=anti_dict_file,
    output_csv="test_sequential.csv",
    distance_max=distance_max
)
time_sequential = time.time() - start_sequential

print(f"\n⏱️  Sequential time: {time_sequential:.2f} seconds")
print()

# Test parallel
print("2️⃣  Running PARALLEL processing...")
start_parallel = time.time()
df_par = generate_submission_parallel(
    books_config=test_config,
    anti_dict_file=anti_dict_file,
    output_csv="test_parallel.csv",
    distance_max=distance_max
)
time_parallel = time.time() - start_parallel

print(f"\n⏱️  Parallel time: {time_parallel:.2f} seconds")
print()

# Compare results
speedup = time_sequential / time_parallel
print("="*60)
print("📊 RESULTS")
print("="*60)
print(f"Sequential: {time_sequential:.2f}s")
print(f"Parallel:   {time_parallel:.2f}s")
print(f"Speedup:    {speedup:.2f}x faster")
print(f"Time saved: {time_sequential - time_parallel:.2f}s")
print()

if speedup > 1.2:
    print("✅ Parallel processing is working efficiently!")
    print(f"   For 37 chapters, estimated time savings: {(time_sequential - time_parallel) * 37/6:.1f}s")
elif speedup > 1.0:
    print("⚠️  Parallel processing is slightly faster, but overhead may be reducing gains")
    print("   This is normal for small datasets. Full dataset will show better speedup.")
else:
    print("❌ Parallel processing is slower - check your system configuration")
    print("   This can happen if:")
    print("   - You only have 1-2 CPU cores")
    print("   - NER models don't support multiprocessing well")
    print("   - System is under heavy load")

print("\n💡 TIP: For best results, run on a machine with 4+ CPU cores")
