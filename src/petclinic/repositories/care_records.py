"""Care_records repository contracts and database-specific implementations."""

from typing import Protocol
from micronaut.context.annotation import Requires
from micronaut.data.jdbc.annotation import JdbcRepository
from micronaut.data.model.query.builder.sql import Dialect
from micronaut.data.repository import CrudRepository
from petclinic.models.care_records import OwnerCareView


@Requires(env=['oracle'])
@JdbcRepository(dialect=Dialect.ORACLE)
class OwnerCareViewRepository(CrudRepository[OwnerCareView, int], Protocol):
    def findOneById(self, id: int) -> OwnerCareView | None: ...
