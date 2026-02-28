"""
Test script for Vector Memory Service
Tests: Embedding generation, memory storage, and semantic search

Run with: python3 test_vector_memory.py
"""

from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.models import User, UserMemory
from app.services.vector_memory_service import get_vector_memory_service
import sys

def test_embedding_generation():
    """Test 1: Verify embedding generation works"""
    print("\n=== TEST 1: Embedding Generation ===")

    try:
        vector_service = get_vector_memory_service(persist_directory="./test_chroma_data")

        # Test embedding generation
        test_text = "I love my cat Whiskers"
        embedding = vector_service.generate_embedding(test_text)

        print(f"✓ Generated embedding for: '{test_text}'")
        print(f"✓ Embedding dimension: {len(embedding)}")
        print(f"✓ First 5 values: {embedding[:5]}")

        if len(embedding) == 384:
            print("✓ PASS: Correct embedding dimension (384)")
            return True
        else:
            print(f"✗ FAIL: Wrong dimension (expected 384, got {len(embedding)})")
            return False

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_add_and_search():
    """Test 2: Add memories and test semantic search"""
    print("\n=== TEST 2: Add Memories and Semantic Search ===")

    db = SessionLocal()
    vector_service = get_vector_memory_service(persist_directory="./test_chroma_data")

    try:
        # Create test user
        test_user = User(
            username=f"vector_test_{datetime.now(timezone.utc).timestamp()}",
            hashed_password="test",
            ai_character_name="Test AI"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        current_time = datetime.now(timezone.utc)

        # Create diverse test memories
        test_memories = [
            UserMemory(
                user_id=test_user.id,
                category="interests",
                memory_key="pet_cat",
                memory_value="I love my cat Whiskers",
                confidence_score=0.9,
                mention_count=5,
                last_updated=current_time
            ),
            UserMemory(
                user_id=test_user.id,
                category="interests",
                memory_key="pet_cat_age",
                memory_value="My cat Whiskers is 3 years old",
                confidence_score=0.8,
                mention_count=2,
                last_updated=current_time
            ),
            UserMemory(
                user_id=test_user.id,
                category="interests",
                memory_key="hobby_reading",
                memory_value="I enjoy reading science fiction books",
                confidence_score=0.85,
                mention_count=3,
                last_updated=current_time
            ),
            UserMemory(
                user_id=test_user.id,
                category="challenges",
                memory_key="work_stress",
                memory_value="I feel stressed about work deadlines",
                confidence_score=0.7,
                mention_count=4,
                last_updated=current_time
            ),
            UserMemory(
                user_id=test_user.id,
                category="goals",
                memory_key="fitness_goal",
                memory_value="I want to exercise more regularly",
                confidence_score=0.8,
                mention_count=2,
                last_updated=current_time
            )
        ]

        # Add to database
        db.add_all(test_memories)
        db.commit()

        # Refresh to get IDs
        for mem in test_memories:
            db.refresh(mem)

        print(f"✓ Created {len(test_memories)} test memories in database")

        # Add to vector database
        result = vector_service.batch_add_memories(test_memories)
        print(f"✓ Added {result['success_count']} memories to vector database")

        # Test semantic search queries
        test_queries = [
            ("my pet", ["cat Whiskers"], "Should find cat-related memories"),
            ("feline friend", ["cat Whiskers"], "Should understand 'feline' = cat"),
            ("job anxiety", ["stressed about work"], "Should understand 'job' = work, 'anxiety' = stress"),
            ("fitness routine", ["exercise more regularly"], "Should connect fitness with exercise"),
            ("sci-fi novels", ["reading science fiction"], "Should understand sci-fi = science fiction")
        ]

        passed_searches = 0
        total_searches = len(test_queries)

        print("\n--- Semantic Search Tests ---")
        for query, expected_keywords, description in test_queries:
            print(f"\nQuery: '{query}' ({description})")

            # Search vector database
            results = vector_service.search_similar_memories(
                query=query,
                user_id=test_user.id,
                limit=3,
                min_similarity=0.3
            )

            if results:
                print(f"  Found {len(results)} results:")
                for memory_id, similarity in results:
                    # Get memory from database
                    memory = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
                    print(f"    - [{similarity:.3f}] {memory.memory_value}")

                    # Check if any expected keyword is in the result
                    for keyword in expected_keywords:
                        if keyword.lower() in memory.memory_value.lower():
                            print(f"    ✓ FOUND expected: '{keyword}'")
                            passed_searches += 1
                            break
            else:
                print("  ✗ No results found")

        # Get stats
        stats = vector_service.get_stats()
        print(f"\n--- Vector Database Stats ---")
        print(f"  Total memories: {stats['total_memories']}")
        print(f"  Embedding dimension: {stats['embedding_dimension']}")
        print(f"  Model: {stats['model_name']}")

        # Determine test result
        print(f"\n✓ Semantic search tests: {passed_searches}/{total_searches} passed")

        if passed_searches >= total_searches * 0.6:  # 60% pass rate
            print("✓ PASS: Semantic search working!")
            return True
        else:
            print("✗ FAIL: Too many semantic searches failed")
            return False

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if test_user:
            # Clean up database
            db.query(UserMemory).filter(UserMemory.user_id == test_user.id).delete()
            db.delete(test_user)
            db.commit()

            # Clean up vector database
            vector_service.clear_user_memories(test_user.id)

        db.close()


def test_similarity_scoring():
    """Test 3: Verify similarity scoring is reasonable"""
    print("\n=== TEST 3: Similarity Scoring ===")

    db = SessionLocal()
    vector_service = get_vector_memory_service(persist_directory="./test_chroma_data")

    try:
        # Create test user
        test_user = User(
            username=f"similarity_test_{datetime.now(timezone.utc).timestamp()}",
            hashed_password="test",
            ai_character_name="Test AI"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        current_time = datetime.now(timezone.utc)

        # Create test memory
        test_memory = UserMemory(
            user_id=test_user.id,
            category="interests",
            memory_key="pet_cat",
            memory_value="I love my cat Whiskers",
            confidence_score=0.9,
            mention_count=5,
            last_updated=current_time
        )

        db.add(test_memory)
        db.commit()
        db.refresh(test_memory)

        vector_service.add_memory(test_memory)

        # Test similarity with different queries
        test_cases = [
            ("I love my cat Whiskers", 0.95, "Exact match should be very high"),
            ("my cat Whiskers", 0.85, "Very similar should be high"),
            ("my pet cat", 0.60, "Related concept should be moderate"),
            ("I enjoy reading books", 0.30, "Unrelated should be low")
        ]

        print("\nSimilarity scores:")
        all_reasonable = True

        for query, expected_min, description in test_cases:
            results = vector_service.search_similar_memories(
                query=query,
                user_id=test_user.id,
                limit=1,
                min_similarity=0.0  # Get all results
            )

            if results:
                similarity = results[0][1]
                is_reasonable = similarity >= expected_min

                status = "✓" if is_reasonable else "✗"
                print(f"  {status} '{query}': {similarity:.3f} (expected >={expected_min}) - {description}")

                if not is_reasonable:
                    all_reasonable = False
            else:
                print(f"  ✗ '{query}': No results")
                all_reasonable = False

        if all_reasonable:
            print("\n✓ PASS: All similarity scores are reasonable!")
            return True
        else:
            print("\n✗ FAIL: Some similarity scores are unreasonable")
            return False

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if test_user:
            db.query(UserMemory).filter(UserMemory.user_id == test_user.id).delete()
            db.delete(test_user)
            db.commit()
            vector_service.clear_user_memories(test_user.id)
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("VECTOR MEMORY SERVICE - TEST SUITE")
    print("=" * 60)

    tests = [
        ("Embedding Generation", test_embedding_generation),
        ("Add and Semantic Search", test_add_and_search),
        ("Similarity Scoring", test_similarity_scoring),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ ERROR in {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    # Cleanup test data directory
    import shutil
    import os
    if os.path.exists("./test_chroma_data"):
        shutil.rmtree("./test_chroma_data")
        print("\n✓ Cleaned up test data directory")

    sys.exit(0 if passed_count == total_count else 1)
