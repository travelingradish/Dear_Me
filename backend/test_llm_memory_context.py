#!/usr/bin/env python3
"""
Test script to examine how memories are passed to the LLM
This will help us understand if the memory context is properly formatted
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.models import User, UserMemory
from app.services.memory_service import MemoryService
from app.services.llm_service import OllamaLLMService
from datetime import datetime
import json

def test_llm_memory_context():
    """Test how memories are formatted and sent to the LLM"""

    print("=== Testing LLM Memory Context Integration ===\n")

    # Create database session
    db = SessionLocal()

    try:
        # Get the test user
        user = db.query(User).filter(User.username == "Wen").first()
        if not user:
            print("❌ Test user 'Wen' not found")
            return

        print(f"✅ Found user: {user.username} (ID: {user.id})")

        # Initialize services
        memory_service = MemoryService()
        llm_service = OllamaLLMService()

        # Test the exact query from the conversation
        test_message = "What did Nova say about Jackie?"
        print(f"\n🔍 Testing query: '{test_message}'")

        # Get relevant memories (same as in the conversation endpoint)
        current_time = datetime.now()
        user_memories = memory_service.get_relevant_memories(
            user.id, test_message, db,
            current_time=current_time, conversation_type="current"
        )

        print(f"\n📋 Retrieved {len(user_memories)} memories:")
        for i, memory in enumerate(user_memories, 1):
            print(f"  {i}. [{memory.category}] {memory.memory_value}")

        # Test the LLM service to see how it formats the prompt
        print(f"\n🤖 Testing LLM prompt generation...")

        character_name = user.ai_character_name or "AI Assistant"
        conversation_history = []  # Empty for this test
        language = "english"
        model_name = "llama3.1:8b"
        user_age = getattr(user, 'age', 35)  # Default age if not set

        print(f"Parameters:")
        print(f"  - Character: {character_name}")
        print(f"  - User age: {user_age}")
        print(f"  - Language: {language}")
        print(f"  - Model: {model_name}")
        print(f"  - Memories: {len(user_memories)}")

        # Let's examine the LLM service's prompt construction
        # First, let's see if we can inspect the prompt before it's sent

        # Create a mock of the generate_conversation_response to see the prompt
        print(f"\n🔍 Examining LLM prompt construction...")

        # Check if there's a method to get the prompt without calling Ollama
        if hasattr(llm_service, '_construct_prompt') or hasattr(llm_service, 'construct_prompt'):
            print("✅ Found prompt construction method")
        else:
            print("❌ No accessible prompt construction method found")

        # Let's try to call the actual method but catch any errors
        try:
            print(f"\n🚀 Making actual LLM call to see the full process...")

            # Call the actual LLM service (this will hit Ollama)
            response = llm_service.generate_conversation_response(
                message=test_message,
                conversation_history=conversation_history,
                language=language,
                model_name=model_name,
                user_memories=user_memories,
                character_name=character_name,
                user_age=user_age,
                current_time=current_time
            )

            print(f"✅ LLM Response: {response[:200]}...")

        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            print("This might be expected if Ollama isn't running")

        # Let's also inspect the LLM service source code structure
        print(f"\n📚 LLM Service Analysis:")
        print(f"  - Methods: {[method for method in dir(llm_service) if not method.startswith('_')]}")

        # Let's examine the memory formatting specifically
        print(f"\n🔍 Memory Object Analysis:")
        if user_memories:
            sample_memory = user_memories[0]
            print(f"  - Memory type: {type(sample_memory)}")
            print(f"  - Memory attributes: {[attr for attr in dir(sample_memory) if not attr.startswith('_')]}")
            print(f"  - Sample memory content: {sample_memory.memory_value}")
            print(f"  - Category: {sample_memory.category}")
            print(f"  - Confidence: {getattr(sample_memory, 'confidence_score', 'N/A')}")
            print(f"  - Last updated: {getattr(sample_memory, 'last_updated', 'N/A')}")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

def inspect_llm_service():
    """Inspect the LLM service implementation"""

    print("\n=== LLM Service Implementation Analysis ===\n")

    # Let's read the LLM service source to understand how it works
    try:
        llm_service_file = "/Users/wenjuanchen/Dear_Me/backend/app/services/llm_service.py"

        print(f"📖 Reading LLM service implementation...")

        if os.path.exists(llm_service_file):
            with open(llm_service_file, 'r') as f:
                content = f.read()

            # Look for key methods
            if 'generate_conversation_response' in content:
                print("✅ Found generate_conversation_response method")

                # Extract the method (simplified)
                lines = content.split('\n')
                method_start = None
                for i, line in enumerate(lines):
                    if 'def generate_conversation_response' in line:
                        method_start = i
                        break

                if method_start:
                    print(f"📍 Method starts at line {method_start + 1}")

                    # Show first 20 lines of the method
                    print(f"\n📝 Method preview:")
                    for i in range(method_start, min(method_start + 20, len(lines))):
                        print(f"  {i+1:3d}: {lines[i]}")

            # Look for memory-related code
            if 'user_memories' in content:
                print("\n✅ Found user_memories references in LLM service")

                # Count occurrences
                memory_lines = [i+1 for i, line in enumerate(content.split('\n')) if 'user_memories' in line.lower()]
                print(f"📊 user_memories mentioned on lines: {memory_lines}")

        else:
            print(f"❌ LLM service file not found at {llm_service_file}")

    except Exception as e:
        print(f"❌ Failed to inspect LLM service: {e}")

if __name__ == "__main__":
    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)

    print("🚀 Starting LLM Memory Context Test...\n")

    # Run tests
    test_llm_memory_context()
    inspect_llm_service()

    print("\n✅ LLM Memory Context testing completed!")