"""Integration checks for database profiles."""

from petclinic_test_support import DATABASE


def test_database_profile_and_oracle_feature_gates(client, application_context):
    import java

    source = application_context.java_ctx.getBean(java.type('javax.sql.DataSource'))
    source = java.type('io.micronaut.data.connection.jdbc.advice.DelegatingDataSource').unwrapDataSource(source)
    connection = source.getConnection()
    try:
        assert connection.getMetaData().getDatabaseProductName() == {
            'h2': 'H2', 'mysql': 'MySQL', 'postgres': 'PostgreSQL', 'oracle': 'Oracle'}[DATABASE]
    finally:
        connection.close()
    if DATABASE != 'oracle':
        for path in ('/visits', '/visits/search?fromDate=2026-01-01&toDate=2026-12-31',
                     '/knowledge', '/owners/1/care-record', '/oracle/transaction-priority'):
            assert client.get(path).status_code == 404, path
        for name in ('PetCareKnowledgeService', 'OwnerCareViewService', 'OracleTransactionPriorityService'):
            assert not application_context.java_ctx.containsBean(java.type('petclinic.' + name))
