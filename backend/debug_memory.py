#!/usr/bin/env python3

import sqlite3
import sys
from datetime import datetime

def check_memory_database():
    """Check the current state of UserMemory table"""
    try:
        conn = sqlite3.connect('dear_me.db')
        cursor = conn.cursor()

        print("=== USER MEMORY ANALYSIS ===\n")

        # Get all memories for all users
        cursor.execute("""
            SELECT id, user_id, category, memory_key, memory_value,
                   confidence_score, first_mentioned, last_updated, is_active
            FROM user_memories
            ORDER BY user_id, last_updated DESC
        """)

        memories = cursor.fetchall()

        if not memories:
            print("No memories found in database.")
            return

        print(f"Found {len(memories)} total memories\n")

        # Group by user
        user_memories = {}
        for memory in memories:
            user_id = memory[1]
            if user_id not in user_memories:
                user_memories[user_id] = []
            user_memories[user_id].append(memory)

        for user_id, user_mems in user_memories.items():
            print(f"--- USER {user_id} ({len(user_mems)} memories) ---")

            # Show recent memories first
            for memory in user_mems[:10]:  # Show top 10
                id_, user_id, category, memory_key, memory_value, confidence, created_at, updated_at, is_active = memory

                # Parse dates
                try:
                    first_mentioned = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else None
                    updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00')) if updated_at else None
                    now = datetime.now()

                    # Calculate age
                    if updated:
                        age_hours = (now - updated).total_seconds() / 3600
                        age_str = f"{age_hours:.1f}h ago" if age_hours < 24 else f"{age_hours/24:.1f}d ago"
                    else:
                        age_str = "no timestamp"

                except Exception as e:
                    age_str = "unknown age"

                status = "ACTIVE" if is_active else "INACTIVE"

                print(f"  [{category}] {memory_value[:80]}{'...' if len(memory_value) > 80 else ''}")
                print(f"    Confidence: {confidence:.2f} | Age: {age_str} | {status}")
                print()

            if len(user_mems) > 10:
                print(f"  ... and {len(user_mems) - 10} more memories")
            print()

        conn.close()

    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_memory_database()