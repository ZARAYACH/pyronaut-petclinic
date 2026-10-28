"""Oracle interval queries compiled by Micronaut Data from Python method names."""

from datetime import date
from typing import Annotated

from jakarta.inject import Inject
from micronaut.context.annotation import Requires
from java.time import LocalDate
from micronaut.http import HttpResponse, MediaType
from micronaut.http.annotation import Controller, Get, Produces, QueryValue
from micronaut.views import View

from petclinic.services.clinic import ClinicService

@Controller('/visits')
@Requires(env=['oracle'])
class VisitSearchController:
    clinic_service: Annotated[ClinicService, Inject]


    @Get
    @View("visits/searchVisits")
    def visit_search_page(self) -> dict:
        return {"year": date.today().year}


    @Get("/search")
    @Produces(MediaType.APPLICATION_JSON)
    def search_visits(
        self,
        fromDate: Annotated[str, QueryValue],
        toDate: Annotated[str, QueryValue],
        maxDurationMinutes: Annotated[int, QueryValue(defaultValue="120")] = 120,
        maxFollowUpMonths: Annotated[int, QueryValue(defaultValue="12")] = 12,
    ):
        try:
            start = date.fromisoformat(fromDate)
            end = date.fromisoformat(toDate)
        except ValueError:
            return HttpResponse.badRequest({"message": "Dates must be valid ISO dates (YYYY-MM-DD)."})
        return self.clinic_service.search_visits(LocalDate.parse(start.isoformat()), LocalDate.parse(end.isoformat()),
                                            maxDurationMinutes, maxFollowUpMonths)
