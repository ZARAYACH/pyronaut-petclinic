"""Shared reference fixtures and database-specific SQL helpers."""

import json
import os
import re

DATABASE = os.environ.get('PETCLINIC_TEST_DATABASE', 'oracle')


def _reference_http(application_context):
    import java
    environment = application_context.java_ctx.getEnvironment()
    resource = environment.getResourceAsStream('fixtures/reference-http.json')
    assert resource.isPresent()
    stream = resource.get()
    try:
        return json.loads(bytes((b & 255) for b in stream.readAllBytes()).decode('utf-8'))
    finally:
        stream.close()


def _database_sql(sql):
    if DATABASE != 'postgres':
        return sql
    names = {'VETS', 'LAST_NAME', 'CLINIC_SERVICE_OFFERINGS', 'NAME', 'DESCRIPTION',
             'PRICE', 'DURATION_MINUTES', 'CLINIC_ID', 'SERVICE_CODE'}
    return re.sub(r'\b[A-Z_]+\b', lambda match: '"' + match[0] + '"' if match[0] in names else match[0], sql)
