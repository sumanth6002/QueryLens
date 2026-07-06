"""Automated tests for QueryLens core algorithms."""

import unittest

from services.normalization_algorithms import analyze_normalization
from explain.parser import parse_explain_json, parse_explain_tabular


class NormalizationTests(unittest.TestCase):
    def test_second_normal_form_violation(self):
        result = analyze_normalization(
            attributes=["StudentID", "CourseID", "StudentName", "Grade"],
            functional_dependencies=[
                {"determinants": ["StudentID"], "dependents": ["StudentName"]},
                {"determinants": ["StudentID", "CourseID"], "dependents": ["Grade"]},
            ],
        )
        self.assertFalse(result["normal_forms"]["2NF"]["satisfied"])
        self.assertFalse(result["normal_forms"]["3NF"]["satisfied"])
        self.assertFalse(result["normal_forms"]["BCNF"]["satisfied"])
        self.assertEqual(
            {frozenset(key) for key in result["candidate_keys"]},
            {frozenset(["StudentID", "CourseID"])},
        )

    def test_third_normal_form_violation(self):
        result = analyze_normalization(
            attributes=["EmpID", "DeptID", "DeptName", "Salary"],
            functional_dependencies=[
                {"determinants": ["EmpID"], "dependents": ["DeptID", "Salary"]},
                {"determinants": ["DeptID"], "dependents": ["DeptName"]},
            ],
        )
        self.assertTrue(result["normal_forms"]["2NF"]["satisfied"])
        self.assertFalse(result["normal_forms"]["3NF"]["satisfied"])

    def test_bcnf_violation(self):
        result = analyze_normalization(
            attributes=["StudentID", "Advisor", "Office"],
            functional_dependencies=[
                {"determinants": ["StudentID"], "dependents": ["Advisor"]},
                {"determinants": ["Advisor"], "dependents": ["Office"]},
            ],
        )
        self.assertFalse(result["normal_forms"]["BCNF"]["satisfied"])

    def test_valid_bcnf_schema(self):
        result = analyze_normalization(
            attributes=["OrderID", "ProductID", "Quantity"],
            functional_dependencies=[
                {"determinants": ["OrderID", "ProductID"], "dependents": ["Quantity"]},
            ],
        )
        self.assertTrue(result["normal_forms"]["1NF"]["satisfied"])
        self.assertTrue(result["normal_forms"]["2NF"]["satisfied"])
        self.assertTrue(result["normal_forms"]["3NF"]["satisfied"])
        self.assertTrue(result["normal_forms"]["BCNF"]["satisfied"])


class ExplainParserTests(unittest.TestCase):
    def test_tabular_explain_detects_table_scan(self):
        parsed = parse_explain_tabular([
            {
                "table": "users",
                "type": "ALL",
                "possible_keys": None,
                "key": None,
                "rows": 100,
                "filtered": 100.0,
                "Extra": "Using where",
            }
        ])
        self.assertEqual(parsed["summary"]["table_scans"], 1)
        self.assertTrue(any(issue["category"] == "full_table_scan" for issue in parsed["issues"]))

    def test_json_explain_parses_join(self):
        parsed = parse_explain_json({
            "query_block": {
                "nested_loop": [
                    {"table": {"table_name": "orders", "access_type": "ALL", "rows_examined_per_scan": 10}},
                    {"table": {"table_name": "users", "access_type": "eq_ref", "key": "PRIMARY", "rows_examined_per_scan": 1}},
                ]
            }
        })
        self.assertEqual(parsed["summary"]["total_tables"], 2)
        self.assertGreaterEqual(parsed["summary"]["join_count"], 1)


if __name__ == "__main__":
    unittest.main()
