from elasticsearch import Elasticsearch

# WHY verify_certs=False: local Docker setup uses HTTP, not HTTPS.
# In production (cloud ES), remove this and set up proper TLS.
es = Elasticsearch(
    "http://localhost:9200",
    verify_certs=False,
    request_timeout=30
)

INDEX_NAME = "rag_index"
