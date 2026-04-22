
import argparse
import csv
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from openai import AzureOpenAI
from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError


DATA_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "Software Questions.csv"
DEFAULT_OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "interview_questions")
DEFAULT_EMBEDDING_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


def get_opensearch_client() -> OpenSearch:
    host = os.environ.get("OPENSEARCH_HOST")
    port = int(os.environ.get("OPENSEARCH_PORT", "9200"))
    username = os.environ.get("OPENSEARCH_USERNAME") or os.environ.get("OPENSEARCH_USER")
    password = os.environ.get("OPENSEARCH_PASSWORD")
    use_ssl = _get_bool_env("OPENSEARCH_USE_SSL", False)

    if not host:
        raise RuntimeError("OPENSEARCH_HOST must be set in the environment.")

    auth = None
    if username and password:
        auth = (username, password)

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=use_ssl,
        verify_certs=False,
    )


def get_embedding_client() -> AzureOpenAI:
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")

    if not azure_endpoint or not azure_key:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set.")

    return AzureOpenAI(
        azure_endpoint=azure_endpoint.rstrip("/"),
        api_key=azure_key,
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )


def load_question_dataset(csv_path: Path = DATA_CSV_PATH) -> List[Dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset CSV not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader if row.get("Question")]


def chunked(iterable: Iterable[Any], size: int) -> Iterable[List[Any]]:
    batch: List[Any] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def embed_texts(texts: List[str], model: str = DEFAULT_EMBEDDING_MODEL) -> List[List[float]]:
    client = get_embedding_client()
    response = client.embeddings.create(model=model, input=texts)
    embeddings = [item.embedding for item in response.data]
    return embeddings


def ensure_vector_index(index_name: str = DEFAULT_OPENSEARCH_INDEX, dims: int = 1536) -> None:
    client = get_opensearch_client()
    if client.indices.exists(index=index_name):
        return

    mapping = {
        "mappings": {
            "properties": {
                "question_number": {"type": "integer"},
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "category": {"type": "keyword"},
                "difficulty": {"type": "keyword"},
                "question_vector": {"type": "dense_vector", "dims": dims},
            }
        }
    }
    client.indices.create(index=index_name, body=mapping)


def index_question_vector(
    question_number: int,
    question: str,
    answer: str,
    category: str,
    difficulty: str,
    vector: List[float],
    index_name: str = DEFAULT_OPENSEARCH_INDEX,
) -> None:
    client = get_opensearch_client()
    document = {
        "question_number": question_number,
        "question": question,
        "answer": answer,
        "category": category,
        "difficulty": difficulty.lower(),
        "question_vector": vector,
    }
    client.index(index=index_name, id=str(question_number), body=document, refresh=True)


def ingest_dataset_to_opensearch(
    csv_path: Path = DATA_CSV_PATH,
    index_name: str = DEFAULT_OPENSEARCH_INDEX,
    batch_size: int = 16,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> int:
    rows = load_question_dataset(csv_path)
    if not rows:
        return 0

    ensure_vector_index(index_name=index_name)
    total_indexed = 0

    for batch in chunked(rows, batch_size):
        texts = [row["Question"].strip() for row in batch]
        embeddings = embed_texts(texts, model=embedding_model)

        for row, vector in zip(batch, embeddings):
            number = int(row.get("Question Number", row.get("question_number", "0")) or 0)
            index_question_vector(
                question_number=number,
                question=row.get("Question", "").strip(),
                answer=row.get("Answer", "").strip(),
                category=row.get("Category", "").strip(),
                difficulty=row.get("Difficulty", "medium").strip(),
                vector=vector,
                index_name=index_name,
            )
            total_indexed += 1

    print(f"Indexed {total_indexed} questions into OpenSearch index '{index_name}'.")
    return total_indexed


def search_similar_questions(
    query: str,
    top_k: int = 5,
    index_name: str = DEFAULT_OPENSEARCH_INDEX,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> List[Dict[str, Any]]:
    client = get_opensearch_client()
    query_embedding = embed_texts([query], model=embedding_model)[0]

    bool_query: Dict[str, Any] = {"must": [], "filter": []}
    if category:
        bool_query["filter"].append({"term": {"category": category}})
    if difficulty:
        bool_query["filter"].append({"term": {"difficulty": difficulty.lower()}})

    search_body: Dict[str, Any] = {
        "size": top_k,
        "query": {
            "script_score": {
                "query": {"bool": bool_query},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'question_vector') + 1.0",
                    "params": {"query_vector": query_embedding},
                },
            }
        },
    }

    try:
        response = client.search(index=index_name, body=search_body)
    except NotFoundError:
        return []

    results = []
    for hit in response.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})
        results.append({
            "question_number": source.get("question_number"),
            "question": source.get("question"),
            "answer": source.get("answer"),
            "category": source.get("category"),
            "difficulty": source.get("difficulty"),
            "score": hit.get("_score", 0.0),
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Index the CSV dataset into OpenSearch with vector embeddings.")
    parser.add_argument("--csv", default=str(DATA_CSV_PATH), help="Path to the dataset CSV file.")
    parser.add_argument("--index", default=DEFAULT_OPENSEARCH_INDEX, help="OpenSearch index name.")
    parser.add_argument("--batch-size", type=int, default=16, help="Embedding batch size.")
    parser.add_argument("--query", type=str, help="Optional query to search after ingestion.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of similar questions to return for query.")
    args = parser.parse_args()

    ingest_dataset_to_opensearch(
        csv_path=Path(args.csv),
        index_name=args.index,
        batch_size=args.batch_size,
    )

    if args.query:
        matches = search_similar_questions(
            query=args.query,
            top_k=args.top_k,
            index_name=args.index,
        )
        print("\nSimilar questions:")
        for item in matches:
            print(f"- [{item['score']:.4f}] {item['question']} (Category: {item['category']}, Difficulty: {item['difficulty']})")


if __name__ == "__main__":
    main()
