#!/usr/bin/env python3
"""
Test conversation quality with llama3.1:8b model.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.guided_llm_service import GuidedLLMService

def test_llama_conversation():
    """Test conversation with llama3.1:8b"""
    print("🦙 Testing Conversation with llama3.1:8b...")
    
    llm_service = GuidedLLMService()
    
    # Test the same problematic conversation
    test_conversation = [
        {
            "user": "I am feeling OK.",
            "intent": "ASK_MOOD",
            "history": [
                {"role": "assistant", "content": "Hello! Let's reflect on your day together. How are you feeling today?"}
            ]
        },
        {
            "user": "Not much. Have to travel back to Australia this evening. It's a long flight. I'm a bit stressed",
            "intent": "ASK_ACTIVITIES", 
            "history": []  # Will be filled dynamically
        },
        {
            "user": "Because the flight is very long.",
            "intent": "ASK_CHALLENGES_WINS",
            "history": []  # Will be filled dynamically
        }
    ]
    
    conversation_history = [
        {"role": "assistant", "content": "Hello! Let's reflect on your day together. How are you feeling today?"}
    ]
    
    try:
        for i, turn in enumerate(test_conversation, 1):
            print(f"\n--- Turn {i} ---")
            print(f"User: {turn['user']}")
            
            response, slot_updates, next_intent = llm_service.guide_conversation_turn(
                user_message=turn['user'],
                current_intent=turn['intent'],
                structured_data={},
                conversation_history=conversation_history,
                language="en",
                model_name="llama3.1:8b"
            )
            
            print(f"Assistant: {response}")
            print(f"Next intent: {next_intent}")
            
            # Analyze response quality
            analyze_response(turn['user'], response, i)
            
            # Update conversation history for next turn
            conversation_history.extend([
                {"role": "user", "content": turn['user']},
                {"role": "assistant", "content": response}
            ])
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_response(user_message, assistant_response, turn_number):
    """Analyze response quality"""
    
    # Check for improvements over the original bad responses
    bad_phrases = ["that sounds", "what made today feel like", "what's making it feel particularly long"]
    improvements = []
    
    if turn_number == 1:
        if "OK" not in assistant_response or assistant_response.lower().count("ok") <= 1:
            improvements.append("✅ Doesn't over-echo 'OK'")
        if any(phrase in assistant_response.lower() for phrase in ["just ok", "in-between", "what's been"]):
            improvements.append("✅ Natural response to 'OK'")
    
    if turn_number == 2 and "australia" in user_message.lower():
        if "australia" in assistant_response.lower():
            improvements.append("✅ Acknowledges Australia travel")
        if not any(phrase in assistant_response.lower() for phrase in bad_phrases):
            improvements.append("✅ Avoids repetitive phrases")
    
    if turn_number == 3:
        if "long" not in assistant_response.lower() or assistant_response.lower().count("long") <= 1:
            improvements.append("✅ Doesn't repeat 'long' excessively")
    
    # General quality checks
    word_count = len(assistant_response.split())
    if 15 <= word_count <= 50:
        improvements.append(f"✅ Good length ({word_count} words)")
    
    print(f"  Quality improvements: {', '.join(improvements) if improvements else 'None detected'}")

if __name__ == "__main__":
    success = test_llama_conversation()
    if success:
        print("\n🎉 llama3.1:8b conversation test completed!")
    else:
        print("\n❌ llama3.1:8b conversation test failed")
    sys.exit(0 if success else 1)