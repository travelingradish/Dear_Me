#!/usr/bin/env python3
"""
Debug slot extraction issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from guided_llm_service import GuidedLLMService

def test_slot_extraction():
    """Test slot extraction directly"""
    print("🔍 Testing Slot Extraction...")
    
    llm_service = GuidedLLMService()
    
    # Test each intent with realistic messages
    test_cases = [
        {
            "intent": "ASK_MOOD",
            "message": "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip.",
            "existing_data": {}
        },
        {
            "intent": "ASK_ACTIVITIES", 
            "message": "I spent time today reflecting on our family's housing situation and future plans.",
            "existing_data": {"mood": "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip."}
        },
        {
            "intent": "ASK_CHALLENGES_WINS",
            "message": "The biggest challenge is finding an affordable house near good schools and my work.",
            "existing_data": {
                "mood": "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip.",
                "activities": "I spent time today reflecting on our family's housing situation and future plans."
            }
        },
        {
            "intent": "ASK_GRATITUDE",
            "message": "I'm grateful for this travel experience and quality time to think about what we need.",
            "existing_data": {
                "mood": "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip.",
                "activities": "I spent time today reflecting on our family's housing situation and future plans.",
                "challenges": "The biggest challenge is finding an affordable house near good schools and my work."
            }
        },
        {
            "intent": "ASK_HOPE",
            "message": "I hope we can find the perfect home for our growing children soon.",
            "existing_data": {
                "mood": "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip.",
                "activities": "I spent time today reflecting on our family's housing situation and future plans.",
                "challenges": "The biggest challenge is finding an affordable house near good schools and my work.",
                "gratitude": "I'm grateful for this travel experience and quality time to think about what we need."
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['intent']} ---")
        print(f"Message: {test_case['message']}")
        print(f"Existing data: {test_case['existing_data']}")
        
        extracted = llm_service._extract_slot_data(
            test_case['intent'], 
            test_case['message'], 
            test_case['existing_data']
        )
        
        print(f"Extracted: {extracted}")
        
        # Simulate the merging logic
        updated_data = test_case['existing_data'].copy()
        for key, value in extracted.items():
            if value:
                updated_data[key] = value
        
        print(f"Updated data: {updated_data}")
    
    # Test final diary composition
    print(f"\n📝 Testing Diary Composition...")
    final_data = {
        "mood": "I'm feeling excited but nervous about returning to Australia tonight from my Sri Lanka trip.",
        "activities": "I spent time today reflecting on our family's housing situation and future plans.",
        "challenges": "The biggest challenge is finding an affordable house near good schools and my work.",
        "gratitude": "I'm grateful for this travel experience and quality time to think about what we need.",
        "hope": "I hope we can find the perfect home for our growing children soon."
    }
    
    print(f"Final structured data: {final_data}")
    
    try:
        diary = llm_service.compose_diary_entry(
            structured_data=final_data,
            language="en",
            model_name="llama3.1:8b"
        )
        
        print(f"Generated diary:")
        print("=" * 50)
        print(diary)
        print("=" * 50)
        
        # Check if diary uses the actual conversation content
        content_words = ["Australia", "Sri Lanka", "housing", "affordable", "schools", "grateful", "children"]
        found_words = [word for word in content_words if word.lower() in diary.lower()]
        
        print(f"Content words found in diary: {found_words}")
        
        if len(found_words) >= 3:
            print("✅ Diary appears to use conversation content!")
            return True
        else:
            print("❌ Diary doesn't seem to use conversation content")
            return False
            
    except Exception as e:
        print(f"❌ Error composing diary: {e}")
        return False

if __name__ == "__main__":
    test_slot_extraction()