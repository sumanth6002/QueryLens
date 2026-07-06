import re

from utils.exceptions import ValidationError

MAX_ATTRIBUTES = 12
MAX_DEPENDENCIES = 30
REPEATING_GROUP_PATTERN = re.compile(r"(.+)[_\-](\d+)$|^(phone|skill|tag|item)s?$", re.IGNORECASE)


def _clean_name(value: str, label: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValidationError(f"{label} cannot be empty.")
    return cleaned


def validate_normalization_input(
    attributes: list,
    functional_dependencies: list,
    multivalued_attributes: list | None = None,
) -> tuple[list[str], list[dict], list[str]]:
    if not isinstance(attributes, list) or not attributes:
        raise ValidationError("At least one attribute is required.")

    if len(attributes) > MAX_ATTRIBUTES:
        raise ValidationError(f"A maximum of {MAX_ATTRIBUTES} attributes is supported.")

    cleaned_attributes = []
    seen = set()

    for attribute in attributes:
        name = _clean_name(str(attribute), "Attribute")
        if name in seen:
            raise ValidationError(f"Duplicate attribute: {name}")
        seen.add(name)
        cleaned_attributes.append(name)

    if not isinstance(functional_dependencies, list):
        raise ValidationError("functional_dependencies must be a list.")

    if len(functional_dependencies) > MAX_DEPENDENCIES:
        raise ValidationError(f"A maximum of {MAX_DEPENDENCIES} functional dependencies is supported.")

    cleaned_dependencies = []
    attribute_set = set(cleaned_attributes)

    for index, dependency in enumerate(functional_dependencies, start=1):
        if not isinstance(dependency, dict):
            raise ValidationError(f"Dependency #{index} must be an object.")

        determinants = dependency.get("determinants", [])
        dependents = dependency.get("dependents", [])

        if not determinants or not dependents:
            raise ValidationError(
                f"Dependency #{index} must include non-empty determinants and dependents."
            )

        det = sorted({_clean_name(str(item), "Determinant") for item in determinants})
        dep = sorted({_clean_name(str(item), "Dependent") for item in dependents})

        unknown = (set(det) | set(dep)) - attribute_set
        if unknown:
            raise ValidationError(
                f"Dependency #{index} references unknown attributes: {', '.join(sorted(unknown))}"
            )

        cleaned_dependencies.append({
            "determinants": det,
            "dependents": dep,
        })

    multivalued = []
    if multivalued_attributes:
        for attribute in multivalued_attributes:
            name = _clean_name(str(attribute), "Multivalued attribute")
            if name not in attribute_set:
                raise ValidationError(f"Multivalued attribute '{name}' is not in the attribute list.")
            multivalued.append(name)

    return cleaned_attributes, cleaned_dependencies, multivalued


def detect_repeating_group_attributes(attributes: list[str]) -> list[str]:
    suspects = []

    for attribute in attributes:
        if REPEATING_GROUP_PATTERN.search(attribute):
            suspects.append(attribute)

    return suspects
