from elastic.es_client import es, INDEX_NAME
from langchain_core.documents import Document

try:
    from elasticsearch import BadRequestError as RequestError
except ImportError:
    from elasticsearch.exceptions import RequestError


def create_index():
    """
    Create the Elasticsearch index with the right field mappings.

    WHY 'text' type for content: enables full-text BM25 search (tokenised, scored).
    WHY 'keyword' type for source: exact-match filtering, not full-text search.
    """
    try:
        if not es.indices.exists(index=INDEX_NAME):
            es.indices.create(
                index=INDEX_NAME,
                mappings={
                    "properties": {
                        "text":   {"type": "text"},
                        "source": {"type": "keyword"},
                        "page":   {"type": "integer"}
                    }
                }
            )
            print("Elasticsearch index created ✅")
        else:
            print("Elasticsearch index already exists ⚡")

    except RequestError as e:
        print(f"❌ Elasticsearch rejected the request")
        print(f"Reason: {e.info if hasattr(e, 'info') else e}")
    except Exception as e:
        print(f"Unexpected error creating index: {e}")


def index_documents(chunks: list):
    """
    Bulk-index all chunks into Elasticsearch.
    Each chunk stores its text, source filename, and page number.
    """
    for i, chunk in enumerate(chunks):
        doc = {
            "text":   chunk.page_content,
            "source": chunk.metadata.get("source", "unknown"),
            "page":   chunk.metadata.get("page", 0)
        }
        es.index(index=INDEX_NAME, id=i, document=doc)

    print(f"Indexed {len(chunks)} chunks into Elasticsearch ✅")


# ─────────────────────────────────────────────
# PHASE 2 — BM25 Search
# ─────────────────────────────────────────────

def bm25_search(query: str, top_k: int = 20) -> list[Document]:
    """
    Run a BM25 keyword search against Elasticsearch.

    WHY BM25 complements vector search:
    - Vector search finds SEMANTICALLY similar chunks ("car" matches "automobile")
    - BM25 finds EXACT keyword matches ("GPT-4" matches "GPT-4", not "language model")
    - Together they catch what the other misses

    WHY 'multi_match': searches across all text fields with BM25 scoring.
    'best_fields' means the highest-scoring field wins (good for short queries).

    Returns a list of LangChain Document objects so RRF can treat both
    retrieval results uniformly.
    """
    response = es.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["text"],
                    "type": "best_fields"
                }
            },
            "size": top_k
        }
    )

    documents = []
    for hit in response["hits"]["hits"]:
        doc = Document(
            page_content=hit["_source"]["text"],
            metadata={
                "source": hit["_source"].get("source", "unknown"),
                "page":   hit["_source"].get("page", 0),
                "bm25_score": hit["_score"]   # store for debugging
            }
        )
        documents.append(doc)

    return documents
