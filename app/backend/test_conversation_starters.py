#!/usr/bin/env python3
"""
Test script for conversation starters functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.conversation_starters_service import conversation_starters_service

def test_conversation_starters():
    print("Testing Conversation Starters Service...")
    
    # Test library name
    test_library = "vi-test-library-index"
    
    print(f"\n1. Testing get_library_starters for '{test_library}':")
    starters = conversation_starters_service.get_library_starters(test_library)
    print(f"Found {len(starters)} starters:")
    for i, starter in enumerate(starters):
        print(f"  {i+1}. {starter['text']}")
    
    print(f"\n2. Testing save_library_starters for '{test_library}':")
    test_starters = [
        {"text": "Test Question 1?", "value": "Test Question 1?"},
        {"text": "Test Question 2?", "value": "Test Question 2?"},
        {"text": "Test Question 3?", "value": "Test Question 3?"}
    ]
    
    try:
        conversation_starters_service.save_library_starters(test_library, test_starters)
        print("Successfully saved test starters")
    except Exception as e:
        print(f"Failed to save starters: {e}")
        return False
    
    print(f"\n3. Verifying saved starters for '{test_library}':")
    saved_starters = conversation_starters_service.get_library_starters(test_library)
    print(f"Found {len(saved_starters)} saved starters:")
    for i, starter in enumerate(saved_starters):
        print(f"  {i+1}. {starter['text']}")
    
    print(f"\n4. Testing get_all_libraries_starters:")
    all_starters = conversation_starters_service.get_all_libraries_starters()
    print(f"Found starters for {len(all_starters)} libraries:")
    for library, starters in all_starters.items():
        print(f"  {library}: {len(starters)} starters")
    
    print(f"\n5. Cleaning up test data:")
    try:
        conversation_starters_service.delete_library_starters(test_library)
        print("Successfully cleaned up test data")
    except Exception as e:
        print(f"Failed to clean up: {e}")
    
    print("\nAll tests completed successfully!")
    return True

if __name__ == "__main__":
    test_conversation_starters()