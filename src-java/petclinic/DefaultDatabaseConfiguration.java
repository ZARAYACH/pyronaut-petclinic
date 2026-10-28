package petclinic;

import io.micronaut.context.ApplicationContextBuilder;
import io.micronaut.context.ApplicationContextConfigurer;
import io.micronaut.context.annotation.ContextConfigurer;
import io.micronaut.context.env.PropertySource;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/** Supply H2 defaults only when no datasource dialect has been configured. */
@ContextConfigurer
public final class DefaultDatabaseConfiguration implements ApplicationContextConfigurer {
    private static final String DEFAULT_DIALECT_PROPERTY = "datasources.default.dialect";

    @Override
    public void configure(ApplicationContextBuilder builder) {
        // Inspect loaded sources before property processing and bean creation.
        // Custom profile names and programmatic overrides must also suppress H2.
        builder.propertySourcesLocator(environment -> {
            if (environment.getPropertySources().stream().anyMatch(DefaultDatabaseConfiguration::hasDialect)) {
                return List.of();
            }
            return environment.getPropertySourceLoaders().stream()
                    .filter(loader -> loader.getExtensions().contains("toml"))
                    .map(loader -> loader.load("application-h2", environment))
                    .flatMap(Optional::stream)
                    .toList();
        });
    }

    private static boolean hasDialect(PropertySource source) {
        if (source.get(DEFAULT_DIALECT_PROPERTY) != null
                || source.get("DATASOURCES_DEFAULT_DIALECT") != null) {
            return true;
        }
        // TOML/YAML property sources can retain their nested map representation.
        return source.get("datasources") instanceof Map<?, ?> datasources
                && datasources.get("default") instanceof Map<?, ?> datasource
                && datasource.containsKey("dialect");
    }
}
