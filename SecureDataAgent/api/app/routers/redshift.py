from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

router = APIRouter(prefix="/redshift", tags=["Redshift Data Service"])

class QueryRequest(BaseModel):
    query: str = Field(..., description="Read-only SQL query to execute")
    database: str = Field(default="analytics", description="Target database name")

class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int

class SchemaResponse(BaseModel):
    tables: List[str]

@router.post(
    "/query",
    response_model=QueryResponse,
    operation_id="redshift_execute_read_query",
    summary="Execute read-only SQL query against Redshift",
    description="Executes a SELECT query against Redshift. DDL and data modification statements are forbidden."
)
def execute_read_query(req: QueryRequest):
    cleaned_query = req.query.strip().upper()
    if not (cleaned_query.startswith("SELECT") or cleaned_query.startswith("WITH")):
        raise HTTPException(status_code=400, detail="Only read-only SELECT or WITH queries are permitted.")
    return QueryResponse(columns=["id", "metric", "val"], rows=[], row_count=0)

@router.get(
    "/schema",
    response_model=SchemaResponse,
    operation_id="redshift_get_schema",
    summary="Get Redshift schema and available tables",
    description="Returns list of authorized table names and view names in the Redshift cluster."
)
def get_schema(database: str = "analytics"):
    return SchemaResponse(tables=["finance.revenue", "finance.expenses", "public.events"])
