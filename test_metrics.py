#!/usr/bin/env python3
"""
Test script to verify Prometheus metrics functionality.
"""

import sys
import time
import requests
from metrics import metrics, start_metrics_server, get_metrics_enabled, get_metrics_port

def test_metrics():
    """Test the metrics functionality."""
    print("Testing Prometheus metrics...")
    
    # Check if metrics are enabled
    if not get_metrics_enabled():
        print("❌ Metrics are disabled in environment")
        return False
    
    print("✅ Metrics are enabled")
    
    # Start metrics server
    port = get_metrics_port()
    print(f"Starting metrics server on port {port}...")
    
    if not start_metrics_server(port):
        print(f"❌ Failed to start metrics server on port {port}")
        return False
    
    print(f"✅ Metrics server started on port {port}")
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test some metrics
    print("Testing metrics collection...")
    
    # Test page view tracking
    metrics.track_page_view('en')
    metrics.track_page_view('de')
    print("✅ Page view metrics tracked")
    
    # Test file upload tracking
    metrics.track_file_upload(1024000, '.mp3', 'success')
    metrics.track_file_upload(2048000, '.mp4', 'success')
    print("✅ File upload metrics tracked")
    
    # Test transcription tracking
    metrics.track_transcription_start('en', 'base', 1, 2)
    time.sleep(1)
    metrics.track_transcription_complete('en', 'base', 30.5, 'success')
    print("✅ Transcription metrics tracked")
    
    # Test user actions
    metrics.track_user_action('save_changes', 'srt')
    metrics.track_download('srt')
    print("✅ User action metrics tracked")
    
    # Test error tracking
    metrics.track_error('TestError', 'test_component')
    print("✅ Error metrics tracked")
    
    # Test metrics endpoint
    try:
        response = requests.get(f'http://localhost:{port}/metrics', timeout=5)
        if response.status_code == 200:
            print("✅ Metrics endpoint is accessible")
            
            # Check if our metrics are present
            content = response.text
            expected_metrics = [
                'transcription_page_views_total',
                'transcription_file_uploads_total',
                'transcription_jobs_total',
                'transcription_user_actions_total',
                'transcription_downloads_total',
                'transcription_errors_total'
            ]
            
            missing_metrics = []
            for metric in expected_metrics:
                if metric not in content:
                    missing_metrics.append(metric)
            
            if missing_metrics:
                print(f"❌ Missing metrics: {missing_metrics}")
                return False
            else:
                print("✅ All expected metrics are present")
                
            # Show some sample metrics
            print("\n📊 Sample metrics output:")
            lines = content.split('\n')
            for line in lines[:20]:
                if line.startswith('transcription_') and not line.startswith('#'):
                    print(f"  {line}")
            
            return True
        else:
            print(f"❌ Metrics endpoint returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to access metrics endpoint: {e}")
        return False

if __name__ == '__main__':
    success = test_metrics()
    if success:
        print("\n🎉 All metrics tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some metrics tests failed!")
        sys.exit(1)