import sys
import unittest
import urllib.request
import json
import time
import subprocess
import os

# Configuration
BASE_URL = "http://127.0.0.1:8001"
VIDEO_ID = "dQw4w9WgXcQ" # Rick Roll - should have transcripts

class TestYouTubeTranscriptAPI(unittest.TestCase):
    def test_01_health_check(self):
        print(f"Testing {BASE_URL}/ ...")
        with urllib.request.urlopen(f"{BASE_URL}/") as response:
            self.assertEqual(response.status, 200)
            data = json.load(response)
            self.assertIn("message", data)

    def test_02_get_transcript_json_default(self):
        print(f"Testing {BASE_URL}/transcript/{VIDEO_ID} (Default Behavior) ...")
        url = f"{BASE_URL}/transcript/{VIDEO_ID}"
        try:
            with urllib.request.urlopen(url) as response:
                self.assertEqual(response.status, 200)
                data = json.load(response)
                self.assertEqual(data["video_id"], VIDEO_ID)
                # Now default transcript is a string
                self.assertIsInstance(data["transcript"], str)
                self.assertEqual(data["format"], "json")
                self.assertIn("language", data)
                self.assertIn("generated", data)
        except urllib.error.HTTPError as e:
            print(f"Test 02 Failed. Error body: {e.read().decode()}")
            raise e

    def test_03_get_transcript_text(self):
        print(f"Testing {BASE_URL}/transcript/{VIDEO_ID}?format=text ...")
        url = f"{BASE_URL}/transcript/{VIDEO_ID}?format=text"
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.status, 200)
            data = json.load(response)
            self.assertEqual(data["video_id"], VIDEO_ID)
            self.assertIsInstance(data["transcript"], str)
            self.assertEqual(data["format"], "text")
            self.assertTrue(len(data["transcript"]) > 0)

    def test_04_query_param_endpoint_timestamps(self):
        print(f"Testing {BASE_URL}/transcript?video_id={VIDEO_ID}&include_timestamps=true ...")
        url = f"{BASE_URL}/transcript?video_id={VIDEO_ID}&include_timestamps=true"
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.status, 200)
            data = json.load(response)
            self.assertEqual(data["video_id"], VIDEO_ID)
            # Check for segments when timestamps requested
            self.assertIn("segments", data)
            self.assertIsInstance(data["segments"], list)
            self.assertIn("start", data["segments"][0])

    def test_05_invalid_video_id(self):
         # ... existing test ...

        print(f"Testing {BASE_URL}/transcript/INVALID_VIDEO_ID_12345 ...")
        url = f"{BASE_URL}/transcript/INVALID_VIDEO_ID_12345"
        try:
            with urllib.request.urlopen(url) as response:
                self.fail("Should have raised 404")
        except urllib.error.HTTPError as e:
            print(f"Error body: {e.read().decode()}")
            self.assertEqual(e.code, 404)

    def tearDown(self):
        # Add a sleep to ensure server logs are flushed or readable if needed
        pass

if __name__ == '__main__':
    # Start the server in a subprocess
    print("Starting server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001"],
        # stdout=subprocess.DEVNULL, # Keep output visible for debugging if needed, or hide to cleaner output
        # stderr=subprocess.DEVNULL
    )
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5)
    
    try:
        # Run tests
        unittest.main(exit=False)
    except Exception as e:
        print(f"Test Execution Failed: {e}")
    finally:
        # Kill server
        print("Stopping server...")
        server_process.kill()
