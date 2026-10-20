"""Global error views with the reference application's public error details."""

import logging

from java.lang import Throwable
from java.io import PrintWriter, StringWriter
from micronaut.http import HttpRequest, HttpStatus
from micronaut.http.annotation import Error
from micronaut.http.server.exceptions import NotFoundException
from micronaut.views import View

LOG = logging.getLogger(__name__)


@Error(status=HttpStatus.NOT_FOUND, global_=True)
@View('error/404')
def not_found(request: HttpRequest) -> dict:
    return {'path': request.getPath(), 'message': 'Page not found'}


@Error(exception=NotFoundException, global_=True)
@View('error/404')
def missing_entity(request: HttpRequest):
    from micronaut.http import HttpResponse
    return HttpResponse.notFound({'path': request.getPath(), 'message': 'Page not found'})


@Error(global_=True)
@View('error/error')
def server_error(request: HttpRequest, throwable: Throwable) -> dict:
    trace = StringWriter()
    throwable.printStackTrace(PrintWriter(trace))
    LOG.error('Error:\n%s', trace.toString())
    return {'path': request.getPath(), 'message': 'Internal Server Error', 'exception': 'Internal Server Error'}
