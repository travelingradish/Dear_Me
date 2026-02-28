# Vector Memory Enhancement Plan

## Overview
Integrate ChromaDB vector database with sentence-transformers embeddings to enable semantic memory search alongside existing pattern-based extraction.

## Architecture Design

### Technology Stack
- **Vector Database**: ChromaDB (local, embedded, lightweight)
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
  - 384-dimensional embeddings
  - ~22M parameters
  - 5-14k sentences/sec on CPU
  - Max input: 256 tokens

### Hybrid Retrieval Strategy
Combine vector similarity with existing keyword/pattern matching:

```
Final Score = (0.6 × Vector Similarity) + (0.4 × Keyword Score)
              × Temporal Relevance × Frequency Boost
```

## Implementation Phases

### Phase 2A: Setup & Infrastructure (Current)
1. ✅ Research vector database options
2. ⏳ Install dependencies (chromadb, sentence-transformers)
3. ⏳ Create VectorMemoryService class
4. ⏳ Initialize ChromaDB collection for memories

### Phase 2B: Embedding Generation
1. Load sentence-transformer model (all-MiniLM-L6-v2)
2. Generate embeddings for memory_value field
3. Store embeddings in ChromaDB with metadata:
   - user_id
   - memory_id (reference to UserMemory table)
   - category
   - confidence_score
   - last_updated
   - mention_count

### Phase 2C: Hybrid Retrieval Implementation
1. Modify `get_relevant_memories()` to use hybrid approach:
   - Generate query embedding
   - Vector search in ChromaDB (top 20 candidates)
   - Apply existing filters (temporal, frequency)
   - Combine with keyword-based results
   - Re-rank with hybrid scoring

2. Keep existing pattern extraction (still valuable for structured data)

### Phase 2D: Migration & Backward Compatibility
1. Create migration script for existing memories
2. Add vector embedding generation to `store_memories()`
3. Maintain backward compatibility (graceful degradation if ChromaDB unavailable)
4. Add configuration flag to enable/disable vector search

### Phase 2E: Testing & Optimization
1. Test semantic search quality:
   - "stressed at work" → finds "job challenges"
   - "my pet" → finds "my cat Whiskers"
   - "exercise routine" → finds "morning yoga"
2. Benchmark performance (latency, accuracy)
3. Tune hybrid scoring weights
4. Create test suite for vector search

## Database Schema Changes

### New Table: VectorMemoryMetadata (optional, for tracking)
```sql
CREATE TABLE vector_memory_metadata (
    id INTEGER PRIMARY KEY,
    memory_id INTEGER REFERENCES user_memories(id),
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    embedding_dimension INTEGER DEFAULT 384,
    created_at TIMESTAMP,
    UNIQUE(memory_id)
);
```

**Note**: Actual embeddings stored in ChromaDB, this table just tracks metadata.

## File Structure
```
backend/
├── app/
│   ├── services/
│   │   ├── memory_service.py (existing)
│   │   ├── vector_memory_service.py (NEW)
│   │   └── hybrid_memory_service.py (NEW - combines both)
│   └── core/
│       └── vector_store.py (NEW - ChromaDB initialization)
├── chroma_data/ (NEW - ChromaDB storage directory)
└── scripts/
    └── migrate_memories_to_vector.py (NEW)
```

## Configuration

### New Environment Variables
```bash
VECTOR_SEARCH_ENABLED=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./chroma_data
HYBRID_VECTOR_WEIGHT=0.6  # 60% vector, 40% keyword
```

## Benefits

### Semantic Understanding
- **Before**: "car" doesn't match "vehicle"
- **After**: Semantic similarity connects related concepts

### Synonym Handling
- **Before**: "stressed" doesn't match "anxious"
- **After**: Embeddings capture emotional similarity

### Context Awareness
- **Before**: "my pet" only matches if "pet" appears in memory
- **After**: Finds "my cat Whiskers" through semantic understanding

### Multi-language Support
- all-MiniLM-L6-v2 trained on multiple languages
- Better cross-language memory retrieval

## Performance Considerations

### Embedding Generation
- **First-time setup**: ~0.01s per memory (batch processing recommended)
- **Real-time**: ~0.01s per new memory (acceptable for user experience)

### Vector Search
- **ChromaDB query**: ~10-50ms for typical dataset (<10k memories)
- **Total latency**: ~50-100ms (including hybrid scoring)

### Storage
- **Per memory**: 384 floats × 4 bytes = ~1.5KB per embedding
- **1000 memories**: ~1.5MB
- **Very efficient for personal journaling app**

## Rollback Strategy

If vector search underperforms:
1. Configuration flag allows instant disable
2. Existing keyword-based system remains fully functional
3. No data loss (original memories in SQLite untouched)
4. ChromaDB can be deleted without affecting core functionality

## Success Metrics

### Accuracy
- Semantic query recall: >80% (find relevant memories with different wording)
- Precision: >70% (avoid irrelevant results)

### Performance
- Query latency: <100ms for 95th percentile
- Memory overhead: <10MB for typical user

### User Experience
- Better conversation context (AI understands related topics)
- Reduced repetition (finds existing memories despite different phrasing)
- Improved follow-up questions (semantic connections)

## Next Steps

1. Install dependencies
2. Create VectorMemoryService skeleton
3. Test embedding generation with sample memories
4. Implement basic vector search
5. Create hybrid scoring system
6. Test with real conversation scenarios
