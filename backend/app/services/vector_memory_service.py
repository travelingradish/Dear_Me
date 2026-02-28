"""
Vector Memory Service - Semantic search for user memories using ChromaDB and sentence-transformers
"""

import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from sqlalchemy.orm import Session
from app.models.models import UserMemory

class VectorMemoryService:
    """Service for vector-based semantic memory search"""

    def __init__(self, persist_directory: str = "./chroma_data"):
        self.logger = logging.getLogger(__name__)
        self.persist_directory = persist_directory

        # Initialize sentence-transformer model
        try:
            self.logger.info("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            self.embedding_dimension = 384  # all-MiniLM-L6-v2 output dimension
            self.logger.info("✓ Embedding model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise

        # Initialize ChromaDB client
        try:
            self.logger.info(f"Initializing ChromaDB (persist_directory: {persist_directory})...")

            # Create persist directory if it doesn't exist
            os.makedirs(persist_directory, exist_ok=True)

            # Initialize ChromaDB client with persistence
            self.chroma_client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry for privacy
                    allow_reset=True
                )
            )

            # Get or create collection for memories
            self.collection = self.chroma_client.get_or_create_collection(
                name="user_memories",
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )

            self.logger.info(f"✓ ChromaDB initialized (collection size: {self.collection.count()})")

        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        try:
            # sentence-transformers returns numpy array
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            raise

    def add_memory(self, memory: UserMemory) -> bool:
        """Add a memory to the vector database"""
        try:
            # Generate embedding for memory value
            embedding = self.generate_embedding(memory.memory_value)

            # Create unique ID for this memory
            doc_id = f"user_{memory.user_id}_memory_{memory.id}"

            # Prepare metadata
            metadata = {
                "user_id": memory.user_id,
                "memory_id": memory.id,
                "category": memory.category,
                "confidence_score": float(memory.confidence_score),
                "mention_count": memory.mention_count,
                "last_updated": memory.last_updated.isoformat() if memory.last_updated else None,
                "is_active": memory.is_active
            }

            # Add to ChromaDB
            self.collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[memory.memory_value],
                metadatas=[metadata]
            )

            self.logger.debug(f"✓ Added memory {memory.id} to vector database")
            return True

        except Exception as e:
            self.logger.error(f"Error adding memory to vector database: {e}")
            return False

    def update_memory(self, memory: UserMemory) -> bool:
        """Update an existing memory in the vector database"""
        # ChromaDB upsert handles both insert and update
        return self.add_memory(memory)

    def delete_memory(self, user_id: int, memory_id: int) -> bool:
        """Delete a memory from the vector database"""
        try:
            doc_id = f"user_{user_id}_memory_{memory_id}"

            # Check if exists before deleting
            try:
                self.collection.get(ids=[doc_id])
                self.collection.delete(ids=[doc_id])
                self.logger.debug(f"✓ Deleted memory {memory_id} from vector database")
                return True
            except Exception:
                self.logger.debug(f"Memory {memory_id} not found in vector database")
                return False

        except Exception as e:
            self.logger.error(f"Error deleting memory from vector database: {e}")
            return False

    def search_similar_memories(
        self,
        query: str,
        user_id: int,
        limit: int = 20,
        min_similarity: float = 0.3,
        category_filter: Optional[str] = None
    ) -> List[Tuple[int, float]]:
        """
        Search for semantically similar memories

        Returns:
            List of tuples (memory_id, similarity_score) sorted by similarity
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)

            # Build metadata filter (ChromaDB 1.x uses $and operator)
            where_conditions = [
                {"user_id": {"$eq": user_id}},
                {"is_active": {"$eq": True}}
            ]
            if category_filter:
                where_conditions.append({"category": {"$eq": category_filter}})

            where_filter = {"$and": where_conditions}

            # Query ChromaDB for similar memories
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter,
                include=["metadatas", "distances"]
            )

            # Process results
            memory_scores = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for i, metadata in enumerate(results['metadatas'][0]):
                    distance = results['distances'][0][i]

                    # Convert distance to similarity (cosine distance -> similarity)
                    # ChromaDB returns distance in [0, 2] where 0 = identical
                    # Convert to similarity in [0, 1] where 1 = identical
                    similarity = 1 - (distance / 2)

                    # Filter by minimum similarity
                    if similarity >= min_similarity:
                        memory_id = metadata['memory_id']
                        memory_scores.append((memory_id, similarity))

                self.logger.debug(f"✓ Found {len(memory_scores)} similar memories for query: '{query[:50]}...'")

            return memory_scores

        except Exception as e:
            self.logger.error(f"Error searching similar memories: {e}")
            return []

    def batch_add_memories(self, memories: List[UserMemory]) -> Dict[str, int]:
        """Add multiple memories to vector database efficiently"""
        success_count = 0
        error_count = 0

        try:
            # Prepare batch data
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for memory in memories:
                try:
                    # Generate embedding
                    embedding = self.generate_embedding(memory.memory_value)

                    # Prepare data
                    doc_id = f"user_{memory.user_id}_memory_{memory.id}"
                    metadata = {
                        "user_id": memory.user_id,
                        "memory_id": memory.id,
                        "category": memory.category,
                        "confidence_score": float(memory.confidence_score),
                        "mention_count": memory.mention_count,
                        "last_updated": memory.last_updated.isoformat() if memory.last_updated else None,
                        "is_active": memory.is_active
                    }

                    ids.append(doc_id)
                    embeddings.append(embedding)
                    documents.append(memory.memory_value)
                    metadatas.append(metadata)

                except Exception as e:
                    self.logger.error(f"Error preparing memory {memory.id}: {e}")
                    error_count += 1

            # Batch upsert to ChromaDB
            if ids:
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                success_count = len(ids)

            self.logger.info(f"✓ Batch added {success_count} memories to vector database ({error_count} errors)")

        except Exception as e:
            self.logger.error(f"Error in batch add memories: {e}")

        return {
            "success_count": success_count,
            "error_count": error_count,
            "total": success_count + error_count
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            total_count = self.collection.count()

            return {
                "total_memories": total_count,
                "embedding_dimension": self.embedding_dimension,
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {}

    def clear_user_memories(self, user_id: int) -> int:
        """Clear all memories for a specific user from vector database"""
        try:
            # Get all memories for this user (ChromaDB 1.x syntax)
            results = self.collection.get(
                where={"user_id": {"$eq": user_id}},
                include=["metadatas"]
            )

            if results and results['ids']:
                # Delete all matching IDs
                self.collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                self.logger.info(f"✓ Cleared {deleted_count} memories for user {user_id}")
                return deleted_count

            return 0

        except Exception as e:
            self.logger.error(f"Error clearing user memories: {e}")
            return 0

    def reset_database(self) -> bool:
        """Reset the entire vector database (USE WITH CAUTION)"""
        try:
            self.logger.warning("⚠️  Resetting entire vector database...")
            self.chroma_client.reset()

            # Re-create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="user_memories",
                metadata={"hnsw:space": "cosine"}
            )

            self.logger.info("✓ Vector database reset complete")
            return True

        except Exception as e:
            self.logger.error(f"Error resetting database: {e}")
            return False


# Singleton instance for reuse across application
_vector_memory_service_instance = None

def get_vector_memory_service(persist_directory: str = "./chroma_data") -> VectorMemoryService:
    """Get singleton instance of VectorMemoryService"""
    global _vector_memory_service_instance

    if _vector_memory_service_instance is None:
        _vector_memory_service_instance = VectorMemoryService(persist_directory)

    return _vector_memory_service_instance
