from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

router = APIRouter(prefix="/postgres", tags=["Postgres Data Service"])

class PostgresQueryRequest(BaseModel):
    query: str = Field(..., description="Read-only SQL query to execute")
    database: str = Field(default="appdb", description="Database name")

class PostgresQueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int

class PostgresSchemaResponse(BaseModel):
    tables: List[str]

@router.post(
    "/query",
    response_model=PostgresQueryResponse,
    operation_id="postgres_execute_read_query",
    summary="Execute read-only SQL query against PostgreSQL",
    description="Executes a SELECT query against PostgreSQL. DDL and data modification statements are forbidden."
)
def execute_read_query(req: PostgresQueryRequest):
    cleaned_query = req.query.strip().upper()
    if not (cleaned_query.startswith("SELECT") or cleaned_query.startswith("WITH")):
        raise HTTPException(status_code=400, detail="Only read-only SELECT or WITH queries are permitted.")
    return PostgresQueryResponse(columns=["id", "name"], rows=[], row_count=0)

@router.get(
    "/schema",
    response_model=PostgresSchemaResponse,
    operation_id="postgres_get_schema",
    summary="Get PostgreSQL schema and available tables",
    description="Returns list of tables available in PostgreSQL."
)
def get_schema(database: str = "appdb"):
    return PostgresSchemaResponse(tables=["public.users", "public.organizations", "finance.invoices"])
