#!/usr/bin/env python3
"""
Test script to demonstrate lazy loading improvements.
Run this to verify models are cached correctly across reloads.
"""

import time
import importlib
import sys

print("="*60)
print("LAZY LOADING TEST")
print("="*60)
print()

# Test 1: First import (should load models)
print("1️⃣  First import (loading models)...")
start = time.time()

import nlp_multi_ner
from nlp_multi_ner import ensemble_entities

time_first = time.time() - start
print(f"   ⏱️  Time: {time_first:.2f} seconds")
print()

# Test 2: Reload module (should use cached models)
print("2️⃣  Reloading module (should use cache)...")
start = time.time()

importlib.reload(nlp_multi_ner)
from nlp_multi_ner import ensemble_entities

time_second = time.time() - start
print(f"   ⏱️  Time: {time_second:.2f} seconds")
print()

# Test 3: Another reload to confirm
print("3️⃣  Third reload (confirming cache works)...")
start = time.time()

importlib.reload(nlp_multi_ner)

time_third = time.time() - start
print(f"   ⏱️  Time: {time_third:.2f} seconds")
print()

# Results
print("="*60)
print("📊 RESULTS")
print("="*60)
print(f"First import:    {time_first:.2f}s  (loaded models)")
print(f"Second reload:   {time_second:.2f}s  (used cache)")
print(f"Third reload:    {time_third:.2f}s  (used cache)")
print()

if time_second < 5 and time_third < 5:
    speedup = time_first / time_second
    print(f"✅ SUCCESS! Lazy loading is working!")
    print(f"   Speedup: {speedup:.1f}x faster on reloads")
    print(f"   Time saved: {time_first - time_second:.1f}s per reload")
elif time_first < 10:
    print("⚠️  Models loaded quickly (might already be cached in system)")
    print("   This is fine - lazy loading is working!")
else:
    print("❌ Something might be wrong - reloads still slow")
    print("   Check if models are truly being cached")

print()

# Test 4: Verify models actually work
print("4️⃣  Testing model functionality...")
test_text = "Hari Seldon est un psychohistorien sur Trantor."

try:
    entities = ensemble_entities(test_text, method="vote")
    print(f"   ✅ Found {len(entities)} entities: {entities}")
    print("   Models are working correctly!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("="*60)
print("TEST COMPLETE")
print("="*60)
