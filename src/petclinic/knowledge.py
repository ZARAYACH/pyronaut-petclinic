"""Oracle vector retrieval using the reference's checked-in embedding catalog."""

from dataclasses import dataclass
from typing import Annotated, Protocol
from micronaut.context.annotation import Requires
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, VectorStorage
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.model.vector import FloatVector, Vector
from micronaut.data.model.vector.search import Score, ScoringFunction, SearchResults
from micronaut.data.repository import CrudRepository
from micronaut.serde.annotation import Serdeable


@MappedEntity('PET_CARE_DOCUMENTS')
@dataclass
class PetCareDocument:
    title: Annotated[str, MappedProperty("TITLE")]
    source: Annotated[str, MappedProperty("SOURCE")]
    description: Annotated[str, MappedProperty("DESCRIPTION")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@MappedEntity('PET_CARE_CHUNKS')
@dataclass
class PetCareChunk:
    documentId: Annotated[int, MappedProperty("DOCUMENT_ID")]
    documentTitle: Annotated[str, MappedProperty("DOCUMENT_TITLE")]
    documentSource: Annotated[str, MappedProperty("DOCUMENT_SOURCE")]
    topic: Annotated[str, MappedProperty("TOPIC")]
    species: Annotated[str, MappedProperty("SPECIES")]
    chunkIndex: Annotated[int, MappedProperty("CHUNK_INDEX")]
    content: Annotated[str, MappedProperty("CONTENT")]
    embedding: Annotated[FloatVector, VectorStorage(length=384), MappedProperty("EMBEDDING")]
    id: Annotated[int | None, Id, GeneratedValue] = None


@Requires(env=['oracle'])
@JdbcRepository(dialect=Dialect.ORACLE)
class PetCareDocumentRepository(CrudRepository[PetCareDocument, int], Protocol):
    pass


@Requires(env=['oracle'])
@JdbcRepository(dialect=Dialect.ORACLE)
class PetCareChunkRepository(CrudRepository[PetCareChunk, int], Protocol):
    def searchTop5ByEmbeddingNear(self, embedding: Vector, maxDistance: Score,
                                  scoringFunction: ScoringFunction) -> SearchResults[PetCareChunk]: ...


@Serdeable
@dataclass
class PetCareSearchRequest:
    query: str
