"""SQLAlchemy ORM models — import all models so metadata is registered."""

from models.functional_dependency import FunctionalDependencySet
from models.index_recommendation import IndexRecommendation
from models.normalization_report import NormalizationReport
from models.query import Query
from models.query_run import QueryRun
from models.schema_snapshot import SchemaSnapshot
from models.user import User
from models.workspace import Workspace

__all__ = [
    "User",
    "Workspace",
    "SchemaSnapshot",
    "Query",
    "QueryRun",
    "FunctionalDependencySet",
    "NormalizationReport",
    "IndexRecommendation",
]
