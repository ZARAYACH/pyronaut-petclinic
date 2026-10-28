"""Care records application services."""

from typing import Annotated
from jakarta.inject import Inject, Singleton
from micronaut.context.annotation import Requires
from petclinic.care_records import OwnerCareView, OwnerCareViewRepository


@Requires(env=['oracle'])
@Singleton
class OwnerCareViewService:
    repository: Annotated[OwnerCareViewRepository, Inject]

    def find(self, owner_id: int) -> OwnerCareView | None:
        return self.repository.findOneById(owner_id)

    def update(self, document: OwnerCareView) -> OwnerCareView | None:
        self.repository.update(document)
        return self.find(document.id)
