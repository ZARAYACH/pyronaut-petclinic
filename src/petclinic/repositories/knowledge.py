"""Knowledge repository contracts and database-specific implementations."""

from typing import Protocol
from micronaut.context.annotation import Requires
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.model.vector import Vector
from micronaut.data.model.vector.search import Score, ScoringFunction, SearchResults
from micronaut.data.repository import CrudRepository
from petclinic.models.knowledge import PetCareDocument, PetCareChunk


@Requires(env=['oracle'])
@JdbcRepository(dialect=Dialect.ORACLE)
class PetCareDocumentRepository(CrudRepository[PetCareDocument, int], Protocol):
    pass


@Requires(env=['oracle'])
@JdbcRepository(dialect=Dialect.ORACLE)
class PetCareChunkRepository(CrudRepository[PetCareChunk, int], Protocol):
    def searchTop5ByEmbeddingNear(self, embedding: Vector, maxDistance: Score,
                                  scoringFunction: ScoringFunction) -> SearchResults[PetCareChunk]: ...
