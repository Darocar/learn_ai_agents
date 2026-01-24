"""Content indexer inbound ports."""

from .source_ingestion import SourceIngestionInboundPort
from .document_splitting import DocumentSplittingInboundPort

__all__ = [
    "SourceIngestionInboundPort",
    "DocumentSplittingInboundPort",
]
