from __future__ import annotations

from itertools import combinations
from typing import Iterable

from utils.normalization_validators import detect_repeating_group_attributes


def _fd_list(functional_dependencies: list[dict]) -> list[tuple[frozenset[str], frozenset[str]]]:
    parsed = []

    for dependency in functional_dependencies:
        determinant = frozenset(dependency["determinants"])
        dependents = frozenset(dependency["dependents"])
        parsed.append((determinant, dependents))

    return parsed


def attribute_closure(seed: Iterable[str], functional_dependencies: list[dict]) -> list[str]:
    closure = set(seed)

    changed = True
    while changed:
        changed = False
        for determinant, dependents in _fd_list(functional_dependencies):
            if determinant.issubset(closure):
                before = len(closure)
                closure |= dependents
                if len(closure) > before:
                    changed = True

    return sorted(closure)


def is_superkey(
    candidate: Iterable[str],
    all_attributes: list[str],
    functional_dependencies: list[dict],
) -> bool:
    return set(attribute_closure(candidate, functional_dependencies)) == set(all_attributes)


def find_candidate_keys(
    all_attributes: list[str],
    functional_dependencies: list[dict],
) -> list[list[str]]:
    attribute_set = set(all_attributes)
    minimal_keys: list[set[str]] = []

    for size in range(1, len(all_attributes) + 1):
        for combo in combinations(all_attributes, size):
            key = set(combo)

            if not is_superkey(key, all_attributes, functional_dependencies):
                continue

            if any(existing.issubset(key) and existing != key for existing in minimal_keys):
                continue

            minimal_keys = [existing for existing in minimal_keys if not key < existing]
            minimal_keys.append(key)

    return [sorted(key) for key in minimal_keys]


def find_superkeys(
    all_attributes: list[str],
    functional_dependencies: list[dict],
    *,
    limit: int = 64,
) -> list[list[str]]:
    superkeys: list[list[str]] = []

    for size in range(1, len(all_attributes) + 1):
        for combo in combinations(all_attributes, size):
            if is_superkey(combo, all_attributes, functional_dependencies):
                superkeys.append(sorted(combo))
                if len(superkeys) >= limit:
                    return superkeys

    return superkeys


def prime_attributes(candidate_keys: list[list[str]]) -> list[str]:
    primes: set[str] = set()
    for key in candidate_keys:
        primes.update(key)
    return sorted(primes)


def build_closure_map(
    all_attributes: list[str],
    functional_dependencies: list[dict],
) -> dict[str, list[str]]:
    return {
        attribute: attribute_closure([attribute], functional_dependencies)
        for attribute in all_attributes
    }


def _expand_atomic_fds(functional_dependencies: list[dict]) -> list[tuple[set[str], str]]:
    atomic = []

    for dependency in functional_dependencies:
        determinant = set(dependency["determinants"])
        for dependent in dependency["dependents"]:
            atomic.append((determinant, dependent))

    return atomic


def check_2nf(
    all_attributes: list[str],
    functional_dependencies: list[dict],
    candidate_keys: list[list[str]],
    prime_attrs: set[str],
) -> dict:
    violations = []

    if all(len(key) == 1 for key in candidate_keys):
        return {
            "satisfied": True,
            "violations": [],
            "explanation": "2NF is satisfied because all candidate keys are single-attribute.",
        }

    for determinant, dependent in _expand_atomic_fds(functional_dependencies):
        if dependent in prime_attrs:
            continue

        for key in candidate_keys:
            key_set = set(key)
            if determinant.issubset(key_set) and determinant != key_set:
                violations.append({
                    "determinants": sorted(determinant),
                    "dependent": dependent,
                    "candidate_key": key,
                    "explanation": (
                        f"Partial dependency: non-prime attribute '{dependent}' depends on "
                        f"{sorted(determinant)}, which is a proper subset of candidate key {key}."
                    ),
                })

    return {
        "satisfied": len(violations) == 0,
        "violations": violations,
        "explanation": (
            "2NF is satisfied; every non-prime attribute depends on the whole candidate key."
            if not violations
            else "2NF is violated because at least one non-prime attribute depends on part of a candidate key."
        ),
    }


def check_3nf(
    functional_dependencies: list[dict],
    prime_attrs: set[str],
    all_attributes: list[str],
) -> dict:
    violations = []

    for determinant, dependent in _expand_atomic_fds(functional_dependencies):
        if dependent in prime_attrs:
            continue

        if not is_superkey(determinant, all_attributes, functional_dependencies):
            violations.append({
                "determinants": sorted(determinant),
                "dependent": dependent,
                "explanation": (
                    f"Transitive dependency: '{dependent}' is non-prime and depends on "
                    f"{sorted(determinant)}, which is not a superkey."
                ),
            })

    return {
        "satisfied": len(violations) == 0,
        "violations": violations,
        "explanation": (
            "3NF is satisfied; every dependency either has a superkey determinant or a prime dependent."
            if not violations
            else "3NF is violated because a non-prime attribute depends on a non-superkey."
        ),
    }


def check_bcnf(
    functional_dependencies: list[dict],
    all_attributes: list[str],
) -> dict:
    violations = []

    for determinant, dependent in _expand_atomic_fds(functional_dependencies):
        if is_superkey(determinant, all_attributes, functional_dependencies):
            continue

        violations.append({
            "determinants": sorted(determinant),
            "dependent": dependent,
            "explanation": (
                f"BCNF violation: determinant {sorted(determinant)} is not a superkey but determines '{dependent}'."
            ),
        })

    return {
        "satisfied": len(violations) == 0,
        "violations": violations,
        "explanation": (
            "BCNF is satisfied; every determinant is a superkey."
            if not violations
            else "BCNF is violated because at least one determinant is not a superkey."
        ),
    }


def check_1nf(
    all_attributes: list[str],
    multivalued_attributes: list[str],
    repeating_group_attributes: list[str],
) -> dict:
    violations = []

    for attribute in multivalued_attributes:
        violations.append({
            "attribute": attribute,
            "explanation": (
                f"Attribute '{attribute}' is marked as multivalued, which violates 1NF atomicity."
            ),
        })

    for attribute in repeating_group_attributes:
        if attribute in multivalued_attributes:
            continue
        violations.append({
            "attribute": attribute,
            "explanation": (
                f"Attribute '{attribute}' appears to represent a repeating group, which violates 1NF."
            ),
        })

    return {
        "satisfied": len(violations) == 0,
        "violations": violations,
        "explanation": (
            "1NF is satisfied; all attributes are atomic."
            if not violations
            else "1NF is violated because at least one attribute is multivalued or non-atomic."
        ),
    }


def analyze_normalization(
    attributes: list[str],
    functional_dependencies: list[dict],
    multivalued_attributes: list[str] | None = None,
    closure_of: list[str] | None = None,
) -> dict:
    multivalued_attributes = multivalued_attributes or []
    repeating_groups = detect_repeating_group_attributes(attributes)

    candidate_keys = find_candidate_keys(attributes, functional_dependencies)
    if not candidate_keys:
        raise ValueError("No candidate key could be derived from the supplied functional dependencies.")

    primes = set(prime_attributes(candidate_keys))
    non_prime = sorted(set(attributes) - primes)
    superkeys = find_superkeys(attributes, functional_dependencies)
    closure_map = build_closure_map(attributes, functional_dependencies)

    requested_closure = None
    if closure_of:
        requested_closure = {
            "seed": sorted(set(closure_of)),
            "closure": attribute_closure(closure_of, functional_dependencies),
        }

    return {
        "attributes": attributes,
        "functional_dependencies": functional_dependencies,
        "attribute_closure": closure_map,
        "requested_closure": requested_closure,
        "candidate_keys": candidate_keys,
        "superkeys": superkeys,
        "prime_attributes": sorted(primes),
        "non_prime_attributes": non_prime,
        "normal_forms": {
            "1NF": check_1nf(attributes, multivalued_attributes, repeating_groups),
            "2NF": check_2nf(attributes, functional_dependencies, candidate_keys, primes),
            "3NF": check_3nf(functional_dependencies, primes, attributes),
            "BCNF": check_bcnf(functional_dependencies, attributes),
        },
    }
