#!/usr/bin/env python3
"""Script to test the improved diary generation"""

import sys
import os

# Add the backend directory to Python path
sys.path.append('/Users/wenjuanchen/daily_check_in_v2/backend')

from app.services.llm_service import OllamaLLMService

def test_diary_generation():
    """Test the improved diary generation with sample data"""
    
    llm_service = OllamaLLMService()
    
    # Sample user responses (what would come from a real conversation)
    sample_answers = {
        "mood": "I'm feeling quite good today, a bit tired but satisfied",
        "activities": "I worked on implementing calendar functionality for my app and had lunch with a friend",
        "challenges": "Dealing with some technical bugs was frustrating, but I solved them",
        "gratitude": "I'm grateful for my friend's support and the progress I made on my project",
        "progress": "Successfully added a working calendar feature to the daily check-in app"
    }
    
    # Sample conversation history (what the user actually said)
    sample_conversation = [
        {"type": "user", "message": "Hi, I had a productive day working on my coding project"},
        {"type": "assistant", "message": "That sounds great! What kind of progress did you make?"},
        {"type": "user", "message": "I managed to add a calendar feature that shows previous diary entries"},
        {"type": "assistant", "message": "How are you feeling about the work you accomplished?"},
        {"type": "user", "message": "Pretty satisfied, though I ran into some bugs that were annoying"},
        {"type": "assistant", "message": "What helped you push through those challenges?"}
    ]
    
    print("Testing improved diary generation...")
    print("=" * 50)
    
    try:
        # Generate diary entry
        diary_entry = llm_service.generate_diary_entry(
            answers=sample_answers,
            conversation_history=sample_conversation,
            language="en",
            tone="reflective"
        )
        
        print("GENERATED DIARY ENTRY:")
        print("-" * 30)
        print(diary_entry)
        print("-" * 30)
        
        # Check for problematic content
        problematic_indicators = ["July", "October", "Nova", "Sri Lankan", "jet lag", "pool"]
        
        has_problems = any(indicator in diary_entry for indicator in problematic_indicators)
        
        if has_problems:
            print("🚨 WARNING: Diary entry contains potentially irrelevant content!")
        else:
            print("✅ Diary entry looks good - no irrelevant content detected!")
            
        # Check if it focuses on the provided information
        user_topics = ["calendar", "coding", "project", "bugs", "productive", "satisfied"]
        relevant_topics = sum(1 for topic in user_topics if topic.lower() in diary_entry.lower())
        
        print(f"📊 Relevance check: {relevant_topics}/{len(user_topics)} user topics mentioned")
        
        if relevant_topics >= 3:
            print("✅ High relevance to user's actual conversation!")
        else:
            print("⚠️  Low relevance - may need further prompt improvements")
            
    except Exception as e:
        print(f"❌ Error generating diary: {e}")

if __name__ == "__main__":
    test_diary_generation()