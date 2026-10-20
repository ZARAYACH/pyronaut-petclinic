"""Oracle vector retrieval using the reference's checked-in embedding catalog."""

import base64
import json
import struct
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Protocol

from jakarta.inject import Inject, Singleton
from jakarta.transaction import Transactional
from micronaut.context.annotation import Factory, Requires
from micronaut.context.event import ApplicationEventListener, StartupEvent
from micronaut.data.annotation import GeneratedValue, Id, MappedEntity, MappedProperty, VectorStorage
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.model.vector import FloatVector, Vector
from micronaut.data.model.vector.search import Score, ScoringFunction, SearchResults
from micronaut.data.repository import CrudRepository
from micronaut.http import MediaType
from micronaut.http.annotation import Body, Controller, Get, Post, Produces, QueryValue
from micronaut.serde.annotation import Serdeable
from micronaut.views import View

from .resources import ApplicationResources


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


@lru_cache(maxsize=1)
def vector_catalog(data: str) -> dict[str, tuple[float, ...]]:
    vectors = {}
    for number, line in enumerate(data.splitlines(), 1):
        if not line.strip() or line.startswith('#'):
            continue
        fields = line.split('\t')
        if len(fields) != 3 or fields[0] not in ('C', 'Q'):
            raise ValueError(f'Invalid vector resource line {number}')
        text = base64.b64decode(fields[1], validate=True).decode('utf-8')
        data = base64.b64decode(fields[2], validate=True)
        if len(data) != 384 * 4:
            raise ValueError(f'Vector resource line {number} must contain 384 floats')
        vectors[text] = struct.unpack('>384f', data)
    if not vectors:
        raise ValueError('No precomputed pet-care vectors found')
    return vectors


@Requires(env=['oracle'])
@Singleton
class StaticPetCareEmbeddingService:
    resources: Annotated[ApplicationResources, Inject]

    def find(self, text: str) -> FloatVector | None:
        values = vector_catalog(self.resources.text('knowledge/pet-care-embeddings.tsv')).get(text.strip()) if text and text.strip() else None
        return FloatVector(list(values)) if values is not None else None

    def embed(self, text: str) -> FloatVector:
        if not text or not text.strip():
            return FloatVector([0.0] * 384)
        vector = self.find(text)
        if vector is None:
            raise ValueError('No precomputed pet-care vector for query: ' + text)
        return vector


@Requires(env=['oracle'])
@Singleton
class PetCareKnowledgeService:
    resources: Annotated[ApplicationResources, Inject]
    chunks: Annotated[PetCareChunkRepository, Inject]
    documents: Annotated[PetCareDocumentRepository, Inject]
    embeddings: Annotated[StaticPetCareEmbeddingService, Inject]

    @Transactional
    def seed(self):
        if self.documents.count() > 0 or self.chunks.count() > 0:
            return
        for source in json.loads(self.resources.text('knowledge/pet-care-knowledge.json'))['documents']:
            document = self.documents.save(PetCareDocument(source['title'], source['source'], source['description']))
            for index, chunk in enumerate(source['chunks']):
                self.chunks.save(PetCareChunk(document.id, document.title, document.source,
                    chunk['topic'], chunk['species'], index, chunk['content'], self.embeddings.embed(chunk['content'])))

    def search(self, query: str) -> list[dict]:
        vector = self.embeddings.find(query)
        if vector is None:
            return []
        matches = self.chunks.searchTop5ByEmbeddingNear(vector, Score(2.0), ScoringFunction.COSINE)
        results = []
        for result in matches.results():
            chunk = result.entity()
            similarity = result.similarity()
            results.append({'id': chunk.id, 'documentTitle': chunk.documentTitle,
                'documentSource': chunk.documentSource, 'topic': chunk.topic, 'species': chunk.species,
                'chunkIndex': chunk.chunkIndex, 'content': chunk.content,
                'distance': result.score().value(), 'similarity': similarity.value() if similarity is not None else None})
        return results


@Factory
@Requires(env=['oracle'])
@Requires(property='petclinic.sample-data.enabled', value='true', defaultValue='true')
class PetCareKnowledgeLoader:
    knowledge: Annotated[PetCareKnowledgeService, Inject]

    @Singleton
    def startup_listener(self) -> ApplicationEventListener[StartupEvent]:
        def on_startup(event: StartupEvent):
            self.knowledge.seed()
        return on_startup


@Serdeable
@dataclass
class PetCareSearchRequest:
    query: str


@Controller('/knowledge')
@Requires(env=['oracle'])
class PetCareKnowledgeController:
    knowledge: Annotated[PetCareKnowledgeService, Inject]


    @Get
    @View('knowledge/search')
    def knowledge_page(self, query: Annotated[str, QueryValue(defaultValue='')] = '') -> dict:
        return {'query': query, 'results': self.knowledge.search(query), 'dimensions': 384}


    @Post(value='/search', consumes=MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    def search_knowledge(self, request: Annotated[PetCareSearchRequest, Body]):
        return self.knowledge.search(request.query)
