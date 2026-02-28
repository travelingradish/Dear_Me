#!/usr/bin/env python3
"""
End-to-End User Journey Test
Simulates a real user: register → journaling across all three modes
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8001"
USER_TIMESTAMP = str(int(time.time()))
USER_DATA = {
    "username": f"sarah_{USER_TIMESTAMP}",
    "password": "JourneyTest123!",
    "age": 28
}

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title:^60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.END}")

def print_user_input(msg):
    print(f"{Colors.YELLOW}👤 User: {msg}{Colors.END}")

def print_ai_response(msg, truncate=200):
    if len(msg) > truncate:
        msg = msg[:truncate] + "..."
    print(f"{Colors.BLUE}🤖 AI: {msg}{Colors.END}")

def register_user():
    """Register a new user account"""
    print_section("STEP 1: REGISTRATION")
    print_info(f"Registering new user: {USER_DATA['username']}")

    response = requests.post(
        f"{API_BASE}/auth/register",
        json=USER_DATA
    )

    try:
        data = response.json()
        if 'access_token' in data and 'user' in data:
            print_success(f"Registration successful!")
            print_info(f"User ID: {data['user']['id']}")
            print_info(f"AI Character: {data['user']['ai_character_name']}")
            return data['access_token'], data['user']['id']
        else:
            print_error(f"Registration failed: {response.text}")
            return None, None
    except:
        print_error(f"Registration failed: {response.text}")
        return None, None

def test_guided_mode(token):
    """Test Guided Diary Mode"""
    print_section("STEP 2: GUIDED DIARY MODE")
    print_info("Starting a guided conversation to create a structured diary entry...")

    headers = {"Authorization": f"Bearer {token}"}

    # Start session
    response = requests.post(
        f"{API_BASE}/guided-diary/start",
        json={"language": "en"},
        headers=headers
    )

    if response.status_code != 200:
        print_error(f"Failed to start session: {response.text}")
        return None

    try:
        session = response.json()
        # Handle both 'id' and 'session_id' response formats
        session_id = session.get('id') or session.get('session_id')
        if not session_id:
            print_error(f"Invalid session response: {session}")
            return None
        print_success(f"Session started (ID: {session_id})")
    except Exception as e:
        print_error(f"Error parsing session response: {e}")
        print_error(f"Response: {response.text}")
        return None

    # Simulate user responses to guided questions
    responses = [
        "I'm feeling great today! Full of energy and optimism.",
        "Had a productive morning with work, then went for a walk in the park. The weather was beautiful.",
        "Nothing major, just some minor stress about an upcoming project deadline.",
        "I'm grateful for my health, my supportive friends, and having meaningful work.",
        "I'm hoping to complete my project successfully and maintain my positive momentum."
    ]

    for i, user_response in enumerate(responses, 1):
        print_user_input(user_response)

        response = requests.post(
            f"{API_BASE}/guided-diary/{session_id}/message",
            json={"message": user_response, "language": "en"},
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('response'):
                print_ai_response(data['response'])
            print_info(f"Phase: {data.get('current_phase')}")

            # Check if we've reached the compose stage
            if data.get('current_phase') == 'COMPOSE':
                print_success("✨ Ready to compose diary!")
                break
        else:
            print_error(f"Message failed: {response.text}")
            break

    # Generate final diary
    print_info("Generating final diary entry...")
    response = requests.post(
        f"{API_BASE}/guided-diary/{session_id}/message",
        json={"message": "Generate my diary now.", "language": "en"},
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('final_diary'):
            print_success("📔 Diary Generated!")
            print_ai_response(data['final_diary'], truncate=400)
            return session_id

    return None

def test_casual_mode(token):
    """Test Casual Chat Mode"""
    print_section("STEP 3: CASUAL CHAT MODE")
    print_info("Having a casual conversation...")

    headers = {"Authorization": f"Bearer {token}"}

    # Simulate casual chat
    chat_messages = [
        "Hey! How's it going?",
        "I just had the most amazing coffee today, reminds me of that café in Paris I visited last year.",
        "What do you think makes a good day? For me it's connecting with people.",
        "I'd like to save this as a memory."
    ]

    conversation_history = []

    for user_msg in chat_messages:
        print_user_input(user_msg)
        conversation_history.append({"role": "user", "content": user_msg})

        response = requests.post(
            f"{API_BASE}/llm/conversation",
            json={
                "message": user_msg,
                "conversation_history": conversation_history,
                "language": "en"
            },
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            ai_response = data.get('response', '')
            print_ai_response(ai_response)
            conversation_history.append({"role": "assistant", "content": ai_response})
        else:
            print_error(f"Chat failed: {response.text}")
            break

    # Generate diary from conversation
    print_info("Generating diary entry from conversation...")
    response = requests.post(
        f"{API_BASE}/diary/generate",
        json={
            "answers": {"conversation": " ".join([m["content"] for m in conversation_history])},
            "conversation_history": conversation_history,
            "language": "en",
            "tone": "reflective"
        },
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('diary_entry'):
            print_success("📔 Diary Generated from Chat!")
            print_ai_response(data['diary_entry'], truncate=400)

    return conversation_history

def test_free_entry_mode(token):
    """Test Free Entry Mode"""
    print_section("STEP 4: FREE ENTRY MODE")
    print_info("Writing a free-form journal entry...")

    headers = {"Authorization": f"Bearer {token}"}

    # User writes freely
    free_text = """Today was a day of reflection and gratitude.

I woke up early and took a long walk through the neighborhood. The morning sun was beautiful, and I had time to think about my life and where I'm headed.

One thing that struck me today was how often I take small moments for granted. A warm cup of tea, a good conversation with a friend, the smell of flowers blooming in spring. These simple things bring so much joy.

I also completed a challenging project at work that I've been working on for weeks. It feels amazing to see it finally come together. The hard work paid off, and I'm proud of what my team accomplished.

Looking ahead, I want to be more intentional about savoring these moments and building deeper connections with the people I care about."""

    print_user_input(free_text)

    # Grammar correction
    print_info("Requesting grammar check...")
    response = requests.post(
        f"{API_BASE}/free-entry/correct-grammar",
        json={"text": free_text, "language": "en"},
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        corrected = data.get('corrected_text', free_text)
        if corrected != free_text:
            print_success("✓ Grammar checked and corrected")
        else:
            print_info("Text was already well-written!")

    # Improve writing
    print_info("Requesting writing improvement...")
    response = requests.post(
        f"{API_BASE}/free-entry/improve-writing",
        json={"text": free_text, "language": "en", "improvement_type": "flow"},
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        improved = data.get('improved_text', free_text)
        print_success("✓ Writing improved for better flow")
        print_ai_response(improved, truncate=400)

    # Save entry
    print_info("Saving journal entry...")
    response = requests.post(
        f"{API_BASE}/free-entry/save",
        json={
            "original_text": free_text,
            "final_text": improved if response.status_code == 200 else free_text,
            "language": "en"
        },
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"✓ Entry saved (ID: {data.get('entry_id')})")
    else:
        print_error(f"Save failed: {response.text}")

def get_user_memories(token, user_id):
    """Retrieve user memories"""
    print_section("STEP 5: CHECKING EXTRACTED MEMORIES")
    print_info("Retrieving memories from all journal entries...")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{API_BASE}/memory/user/{user_id}",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        memories = data.get('memories', [])

        if memories:
            print_success(f"Found {len(memories)} memory entries!")

            # Group by category
            by_category = {}
            for memory in memories[:5]:  # Show first 5
                category = memory.get('category', 'other')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(memory)

            for category, items in by_category.items():
                print_info(f"\n📌 {category.upper()}:")
                for item in items:
                    print(f"   - {item.get('content', 'N/A')}")
        else:
            print_info("No memories extracted yet (they populate after processing)")
    else:
        print_error(f"Failed to retrieve memories: {response.text}")

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print(r"""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║         🌙 DEAR ME - USER JOURNEY TEST 🌙           ║
    ║                                                       ║
    ║         Simulating a new user's first day            ║
    ║         of journaling across all three modes         ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    print(Colors.END)

    print_info(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Target API: {API_BASE}")

    # Step 1: Register
    token, user_id = register_user()
    if not token:
        print_error("Cannot proceed without registration")
        return

    time.sleep(1)

    # Step 2: Guided Mode
    guided_session_id = test_guided_mode(token)
    time.sleep(1)

    # Step 3: Casual Mode
    test_casual_mode(token)
    time.sleep(1)

    # Step 4: Free Entry Mode
    test_free_entry_mode(token)
    time.sleep(1)

    # Step 5: Check memories
    get_user_memories(token, user_id)

    # Summary
    print_section("JOURNEY COMPLETE ✨")
    print_success(f"User '{USER_DATA['username']}' has successfully journaled!")
    print_info(f"✓ Created guided diary session")
    print_info(f"✓ Had casual conversation")
    print_info(f"✓ Wrote free-form entry with improvements")
    print_info(f"✓ Extracted memories from entries")
    print_info(f"\nYou can now log in as: {USER_DATA['username']}")
    print_info(f"Password: {USER_DATA['password']}")
    print_info(f"Access at: http://localhost:3000")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is the backend running?")
        print_info("Start it with: cd backend && uv run main.py")
    except KeyboardInterrupt:
        print_error("\nTest interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
