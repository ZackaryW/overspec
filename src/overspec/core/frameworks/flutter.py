"""Flutter SDK plus integration-test evidence."""

from zuu.case13 import deep_get


def detect(evidence):
    document = evidence.document("pubspec.yaml", "yaml")
    if document is None:
        return False
    flutter = integration = False
    for group in ("dependencies", "dev_dependencies"):
        dependencies = deep_get(document, [group], default={})
        if not isinstance(dependencies, dict):
            raise ValueError(f"pubspec.yaml: {group} must be a mapping")  # noqa: TRY004 - malformed user manifest
        for name in ("flutter", "integration_test"):
            value = dependencies.get(name)
            if (
                isinstance(value, dict)
                and deep_get(value, ["sdk"], default=None) == "flutter"
            ):
                flutter |= name == "flutter"
                integration |= name == "integration_test"
    return flutter and (integration or evidence.dart_sources("integration_test"))
