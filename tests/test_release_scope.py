"""Contract tests for authoritative component input and conservative page audit."""

import pytest

from tools.release_scope import Component, audit_document, choose_scope, parse_components


def test_names_repos_namespaces_and_comments():
    assert parse_components("# scope\n\nKafka | canonical/kafka-operator | kafka\n"
                            "canonical/kafka-connect-operator\nKafka UI\n") == [
        Component("Kafka", "canonical/kafka-operator", "kafka"),
        Component("kafka-connect-operator", "canonical/kafka-connect-operator"),
        Component("Kafka UI"),
    ]


def test_file_wins_disagreement_without_merging_lists():
    scope = choose_scope("Kafka | canonical/kafka-operator", "Kafka UI")
    assert scope["source"] == "file"
    assert scope["components"] == [{"name": "Kafka", "repo": "canonical/kafka-operator",
                                    "tag_namespace": None}]
    assert scope["ignored_inline"] == [{"name": "Kafka UI", "repo": None,
                                        "tag_namespace": None}]


@pytest.mark.parametrize("contents", ["", "# only comments", "Kafka\nkafka",
                                       "Kafka | not-a-repo", "Kafka | canonical/a | ",
                                       "Kafka | canonical/a | a | extra", "| canonical/a"])
def test_invalid_file_is_not_replaced_by_valid_inline_list(contents):
    with pytest.raises(ValueError):
        choose_scope(contents, "Kafka | canonical/kafka-operator")


def test_multiple_components_can_share_repo_with_distinct_namespaces():
    assert parse_components("Charm | canonical/multi-operator | charm\n"
                            "Sidecar | canonical/multi-operator | sidecar\n") == [
        Component("Charm", "canonical/multi-operator", "charm"),
        Component("Sidecar", "canonical/multi-operator", "sidecar"),
    ]


def test_detect_static_compatibility_row_outside_selected_scope():
    text = "# Release\n## Kafka\n### Bug fixes\n* fixed thing\n"
    text += "## Compatibility\n| Charm | Revision |\n|---|---|\n"
    text += "| Kafka | 123 |\n| Kafka UI | 45 |\n"
    assert audit_document(text, [Component("Kafka")], ["Kafka UI"]) == {
        "missing": [], "unexpected": ["Kafka UI"]}


def test_unchanged_component_present_only_in_compatibility_is_not_missing():
    text = "## Kafka\n* fixed thing\n## Compatibility\n"
    text += "| Kafka | 123 |\n| [Kafka UI](https://charmhub.io/ui) | 45 |\n"
    assert audit_document(text, [Component("Kafka"), Component("Kafka UI")]) == {
        "missing": [], "unexpected": []}


def test_absent_listed_component_is_reported_not_silently_dropped():
    assert audit_document("## Kafka\n", [Component("Kafka"), Component("Kafka UI")]) == {
        "missing": ["Kafka UI"], "unexpected": []}


def test_review_comment_and_noncompatibility_tables_do_not_satisfy_scope():
    text = "<!--\n## Kafka UI\n| Kafka UI | TODO |\n-->\n"
    text += "## Security\n| Kafka UI | CVE-123 |\n"
    text += "```md\n## Kafka UI\n```\n"
    assert audit_document(text, [Component("Kafka UI")]) == {
        "missing": ["Kafka UI"], "unexpected": []}


def test_spark_eval_rst_grid_compatibility_rows_are_audited():
    text = "## Compatibility\n\n```{eval-rst}\n+-----+-----+\n"
    text += "| Component | Revision |\n+=====+=====+\n"
    text += "| Apache Spark History Server | 5 |\n+-----+-----+\n"
    text += "| Apache Kyuubi | 6 |\n+-----+-----+\n```\n"
    assert audit_document(text, [Component("Apache Kyuubi")],
                          ["Apache Spark History Server"]) == {
        "missing": [], "unexpected": ["Apache Spark History Server"]}