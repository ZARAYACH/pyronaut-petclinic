package petclinic;

import io.micronaut.context.ApplicationContextBuilder;
import io.micronaut.context.ApplicationContextConfigurer;
import io.micronaut.context.annotation.ContextConfigurer;

import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/** Select the H2 configuration only when no database profile is active. */
@ContextConfigurer
public final class DefaultDatabaseConfiguration implements ApplicationContextConfigurer {
    private static final Set<String> DATABASE_PROFILES =
            Set.of("h2", "oracle", "oracle-deepsec", "postgres", "mysql");

    @Override
    public void configure(ApplicationContextBuilder builder) {
        // Pyronaut supplies dev/test environments, so builder.defaultEnvironments
        // alone would not select H2. Resolve the fallback after names are known,
        // before datasource beans or Test Resources resolve any properties.
        builder.propertySourcesLocator(environment -> {
            if (!Collections.disjoint(environment.getActiveNames(), DATABASE_PROFILES)) {
                return List.of();
            }
            return environment.getPropertySourceLoaders().stream()
                    .filter(loader -> loader.getExtensions().contains("toml"))
                    .map(loader -> loader.load("application-h2", environment))
                    .flatMap(Optional::stream)
                    .toList();
        });
    }
}
