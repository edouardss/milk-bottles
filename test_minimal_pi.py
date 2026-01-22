#!/usr/bin/env python3
"""
Minimal test to isolate the illegal instruction error
"""

import sys

print("=" * 60)
print("Minimal Test for Raspberry Pi")
print("=" * 60)
print("")

# Test 1: Basic imports
print("Test 1: Importing packages...")
try:
    import os
    from dotenv import load_dotenv
    import cv2
    from inference import InferencePipeline
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Load environment
print("\nTest 2: Loading environment variables...")
try:
    load_dotenv("config.env")
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if api_key:
        print(f"✓ API key loaded (length: {len(api_key)})")
    else:
        print("✗ API key not found in config.env")
        sys.exit(1)
except Exception as e:
    print(f"✗ Environment load failed: {e}")
    sys.exit(1)

# Test 3: Initialize InferencePipeline (without starting)
print("\nTest 3: Creating InferencePipeline...")
try:
    pipeline = InferencePipeline.init_with_workflow(
        api_key=api_key,
        workspace_name="edss",
        workflow_id="count-milk-alerts",
        video_reference=0,
        max_fps=5,
        on_prediction=lambda result, frame: None  # Dummy callback
    )
    print("✓ Pipeline created successfully")
except Exception as e:
    print(f"✗ Pipeline creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Start pipeline (this might trigger the error)
print("\nTest 4: Starting pipeline...")
print("(Press Ctrl+C to stop after a few seconds)")
try:
    pipeline.start()
    print("✓ Pipeline started")

    # Let it run for 3 seconds
    import time
    time.sleep(3)

    pipeline.terminate()
    print("✓ Pipeline terminated")
except KeyboardInterrupt:
    print("\n✓ Interrupted by user")
    pipeline.terminate()
except Exception as e:
    print(f"✗ Pipeline start failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("All tests passed! The issue is not in the basic pipeline.")
print("=" * 60)
