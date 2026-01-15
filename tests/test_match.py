"""Test the SearchGroup.match function for word boundary scoring."""

import sys

sys.path.insert(0, "src")

from board import SearchGroup


def test_match():
    search = SearchGroup()

    print("Testing exact matches:")
    tests = [
        ("ear", "ear"),
        ("ear ", "ear"),
        (" ear", "ear"),
        (" ear ", "ear"),
    ]
    for text, needle in tests:
        score = search.match(text, needle)
        print(f"  match('{text}', '{needle}') = {score}")

    print("\nTesting matches at word end:")
    tests = [
        ("ears", "ear"),
        (" ears", "ear"),
        ("ears ", "ear"),
        (" ears ", "ear"),
    ]
    for text, needle in tests:
        score = search.match(text, needle)
        print(f"  match('{text}', '{needle}') = {score}")

    print("\nTesting matches within words:")
    tests = [
        ("hear", "ear"),
        (" hear", "ear"),
        ("hear ", "ear"),
        (" hear ", "ear"),
    ]
    for text, needle in tests:
        score = search.match(text, needle)
        print(f"  match('{text}', '{needle}') = {score}")

    print("\nTesting multiple matches:")
    tests = [
        (" ear, hear", "ear"),
        (" ear, hear ", "ear"),
        ("hear, ear", "ear"),
    ]
    for text, needle in tests:
        score = search.match(text, needle)
        print(f"  match('{text}', '{needle}') = {score}")

    print("\nTesting no matches:")
    tests = [
        ("hello", "ear"),
        ("test", "ear"),
    ]
    for text, needle in tests:
        score = search.match(text, needle)
        print(f"  match('{text}', '{needle}') = {score}")


if __name__ == "__main__":
    test_match()
