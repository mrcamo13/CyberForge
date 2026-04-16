"""test_tools_stage2.py — Unit tests for AEGIS Stage 2 dynamic tool functions."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tools import run_tool


class TestTrafficAnalyzer(unittest.TestCase):
    """Tests for traffic_analyzer — beaconing detection."""

    def test_beacon_detected(self):
        """3 records to same dst with equal interval > 0 should produce [BEACON]."""
        data = (
            "2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\n"
            "2026-04-11T03:16:00,10.0.0.99,185.220.101.45,4444,128,30\n"
            "2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,30"
        )
        result = run_tool("traffic_analyzer", data)
        self.assertIn("[BEACON]", result)
        self.assertIn("185.220.101.45", result)

    def test_no_beacon_single_connections(self):
        """All single connections should produce no [BEACON]."""
        data = (
            "2026-04-11T03:15:00,10.0.0.99,203.0.113.47,443,512,0\n"
            "2026-04-11T03:15:30,10.0.0.99,8.8.8.8,53,64,0"
        )
        result = run_tool("traffic_analyzer", data)
        self.assertNotIn("[BEACON]", result)

    def test_no_beacon_unequal_intervals(self):
        """3 records to same dst but unequal intervals should produce no [BEACON]."""
        data = (
            "2026-04-11T03:15:00,10.0.0.99,185.220.101.45,4444,128,10\n"
            "2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\n"
            "2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,60"
        )
        result = run_tool("traffic_analyzer", data)
        self.assertNotIn("[BEACON]", result)

    def test_no_beacon_zero_interval(self):
        """3 records with equal interval=0 should NOT produce [BEACON] (zero excluded)."""
        data = (
            "2026-04-11T03:15:00,10.0.0.99,203.0.113.47,443,512,0\n"
            "2026-04-11T03:15:30,10.0.0.99,203.0.113.47,443,512,0\n"
            "2026-04-11T03:16:00,10.0.0.99,203.0.113.47,443,512,0"
        )
        result = run_tool("traffic_analyzer", data)
        self.assertNotIn("[BEACON]", result)

    def test_escaped_newlines_in_challenge_data(self):
        """challenge_data stored with \\n escape sequences should be handled correctly."""
        data = (
            "2026-04-11T03:15:30,10.0.0.99,185.220.101.45,4444,128,30\\n"
            "2026-04-11T03:16:00,10.0.0.99,185.220.101.45,4444,128,30\\n"
            "2026-04-11T03:16:30,10.0.0.99,185.220.101.45,4444,128,30"
        )
        result = run_tool("traffic_analyzer", data)
        self.assertIn("[BEACON]", result)


class TestIocHunter(unittest.TestCase):
    """Tests for ioc_hunter — IOC correlation against log data."""

    def test_match_found(self):
        """At least one log line matching an IOC should produce [MATCH]."""
        data = (
            "deploymaster,185.220.101.45|||"
            "sshd: Accepted password for deploymaster from 10.0.0.99\n"
            "nginx: GET /login 200"
        )
        result = run_tool("ioc_hunter", data)
        self.assertIn("[MATCH]", result)
        self.assertIn("[NO MATCH]", result)

    def test_no_match(self):
        """No log lines matching any IOC should produce no [MATCH]."""
        data = "unknownIOC|||sshd: normal log line\nnginx: normal log"
        result = run_tool("ioc_hunter", data)
        self.assertNotIn("[MATCH]", result)

    def test_empty_ioc_skipped(self):
        """Trailing comma in IOC list produces empty string which should be skipped."""
        data = "deploymaster,|||sshd: Accepted password for deploymaster"
        result = run_tool("ioc_hunter", data)
        self.assertIn("[MATCH]", result)

    def test_case_sensitive_matching(self):
        """IOC matching is case-sensitive — 'Deploymaster' should not match 'deploymaster'."""
        data = "deploymaster|||sshd: Accepted password for Deploymaster"
        result = run_tool("ioc_hunter", data)
        self.assertNotIn("[MATCH]", result)

    def test_result_count_line(self):
        """Output should include a results count summary line."""
        data = (
            "deploymaster|||"
            "sshd: Accepted password for deploymaster\n"
            "nginx: GET /login"
        )
        result = run_tool("ioc_hunter", data)
        self.assertIn("Results:", result)


class TestAttackMapper(unittest.TestCase):
    """Tests for attack_mapper — MITRE ATT&CK technique lookup."""

    def test_suid_maps_to_t1548_001(self):
        """SUID/root shell description should match T1548.001."""
        result = run_tool("attack_mapper", "SUID bit python3 root shell")
        self.assertIn("T1548.001", result)

    def test_top_match_is_match_not_related(self):
        """T1548.001 should appear as MATCH (not RELATED) for SUID input."""
        result = run_tool("attack_mapper", "SUID bit python3 root shell")
        self.assertIn("MATCH -- T1548.001", result)

    def test_no_match_returns_informative_message(self):
        """Unrecognized description should report no matching techniques."""
        result = run_tool("attack_mapper", "zzz qqq www")
        self.assertIn("No matching techniques found", result)

    def test_multi_word_keyword_match(self):
        """Multi-word keyword 'suid bit' should match via substring search."""
        result = run_tool("attack_mapper", "the suid bit was set on the binary")
        self.assertIn("T1548.001", result)

    def test_top_match_line_present(self):
        """Output should end with 'Top match: <id>' for matched input."""
        result = run_tool("attack_mapper", "suid python3")
        self.assertIn("Top match: T1548.001", result)


class TestRuleAnalyzer(unittest.TestCase):
    """Tests for rule_analyzer — firewall policy evaluation."""

    def test_catch_all_allows_port_8080(self):
        """Port 8080 not explicitly denied should be allowed by catch-all and flagged as GAP."""
        data = (
            "DENY ANY 0.0.0.0/0 203.0.113.47 22\n"
            "ALLOW ANY 0.0.0.0/0 ANY ANY|||"
            "203.0.113.1 203.0.113.47 8080 INBOUND"
        )
        result = run_tool("rule_analyzer", data)
        self.assertIn("ALLOW", result)
        self.assertIn("GAP", result)
        self.assertIn("8080", result)

    def test_explicit_deny_blocks_port_22(self):
        """Explicit DENY rule for port 22 should block matching traffic."""
        data = (
            "DENY ANY 0.0.0.0/0 203.0.113.47 22\n"
            "ALLOW ANY 0.0.0.0/0 ANY ANY|||"
            "203.0.113.1 203.0.113.47 22 INBOUND"
        )
        result = run_tool("rule_analyzer", data)
        self.assertIn("DENY via Rule 1", result)

    def test_explicit_allow_matches_before_catch_all(self):
        """An explicit ALLOW rule should match before the catch-all."""
        data = (
            "ALLOW ANY 0.0.0.0/0 203.0.113.47 443\n"
            "DENY ANY 0.0.0.0/0 ANY ANY|||"
            "203.0.113.44 203.0.113.47 443 INBOUND"
        )
        result = run_tool("rule_analyzer", data)
        self.assertIn("ALLOW via Rule 1", result)

    def test_cidr_src_treated_as_any(self):
        """Rule with SRC=0.0.0.0/0 should match all source IPs."""
        data = (
            "DENY ANY 0.0.0.0/0 ANY 9999|||"
            "1.2.3.4 5.6.7.8 9999 INBOUND"
        )
        result = run_tool("rule_analyzer", data)
        self.assertIn("DENY", result)


class TestRiskScorer(unittest.TestCase):
    """Tests for risk_scorer — likelihood x impact risk matrix."""

    def test_critical_score(self):
        """L=4, I=5 => score 20 => CRITICAL."""
        result = run_tool("risk_scorer", "likelihood:4|impact:5|asset:production|exploited:yes")
        self.assertIn("CRITICAL", result)
        self.assertIn("20", result)

    def test_low_score(self):
        """L=1, I=2 => score 2 => LOW."""
        result = run_tool("risk_scorer", "likelihood:1|impact:2|asset:test|exploited:no")
        self.assertIn("LOW", result)
        self.assertIn("2", result)

    def test_medium_score(self):
        """L=2, I=4 => score 8 => MEDIUM."""
        result = run_tool("risk_scorer", "likelihood:2|impact:4|asset:staging|exploited:no")
        self.assertIn("MEDIUM", result)
        self.assertIn("8", result)

    def test_high_score(self):
        """L=3, I=5 => score 15 => HIGH."""
        result = run_tool("risk_scorer", "likelihood:3|impact:5|asset:production|exploited:no")
        self.assertIn("HIGH", result)
        self.assertIn("15", result)

    def test_exploitation_does_not_change_rating(self):
        """exploited=yes should NOT change the rating band — only adds urgency note."""
        result_yes = run_tool("risk_scorer", "likelihood:2|impact:3|asset:production|exploited:yes")
        result_no = run_tool("risk_scorer", "likelihood:2|impact:3|asset:production|exploited:no")
        self.assertIn("LOW", result_yes)
        self.assertIn("LOW", result_no)

    def test_exploited_yes_adds_urgency_note(self):
        """exploited=yes should include an urgency note in output."""
        result = run_tool("risk_scorer", "likelihood:4|impact:5|asset:production|exploited:yes")
        self.assertIn("urgency", result.lower())

    def test_exploited_no_no_urgency(self):
        """exploited=no should not include SLA emergency line."""
        result = run_tool("risk_scorer", "likelihood:4|impact:5|asset:production|exploited:no")
        self.assertNotIn("SLA: Emergency", result)


class TestRemediationPlanner(unittest.TestCase):
    """Tests for remediation_planner — priority ranking with dependency ordering."""

    def test_highest_ratio_ranked_first(self):
        """Item with highest impact/effort ratio should be RANK 1."""
        data = (
            "item01|patch nginx|EFFORT:1|IMPACT:5|DEPENDENCY:none\n"
            "item02|reset creds|EFFORT:1|IMPACT:4|DEPENDENCY:none"
        )
        result = run_tool("remediation_planner", data)
        lines = result.split("\n")
        rank1_line = [l for l in lines if "RANK 1" in l][0]
        self.assertIn("patch nginx", rank1_line)

    def test_dependency_respected(self):
        """Dependent item (even with higher ratio) must appear after its dependency."""
        data = (
            "item01|low impact item|EFFORT:1|IMPACT:1|DEPENDENCY:none\n"
            "item02|high impact item|EFFORT:1|IMPACT:5|DEPENDENCY:item01"
        )
        result = run_tool("remediation_planner", data)
        idx_item01 = result.index("[item01]")
        idx_item02 = result.index("[item02]")
        self.assertLess(idx_item01, idx_item02)

    def test_dep_free_before_dependent_at_same_ratio(self):
        """At equal ratio, dependency-free items sort before dependent items."""
        data = (
            "item01|dep item|EFFORT:1|IMPACT:3|DEPENDENCY:item02\n"
            "item02|free item|EFFORT:1|IMPACT:3|DEPENDENCY:none"
        )
        result = run_tool("remediation_planner", data)
        idx_item01 = result.index("[item01]")
        idx_item02 = result.index("[item02]")
        self.assertLess(idx_item02, idx_item01)

    def test_case12_full_data(self):
        """Full case12 challenge_data: item01 must be RANK 1, item04 after item01."""
        data = (
            "item01|patch nginx 1.24.0|EFFORT:1|IMPACT:5|DEPENDENCY:none\n"
            "item02|reset deploymaster credentials|EFFORT:1|IMPACT:4|DEPENDENCY:none\n"
            "item03|remove SUID from python3|EFFORT:2|IMPACT:4|DEPENDENCY:none\n"
            "item04|implement WAF rules|EFFORT:3|IMPACT:3|DEPENDENCY:item01\n"
            "item05|network segmentation|EFFORT:5|IMPACT:5|DEPENDENCY:none\n"
            "item06|security awareness training|EFFORT:4|IMPACT:2|DEPENDENCY:none"
        )
        result = run_tool("remediation_planner", data)
        lines = result.split("\n")
        rank1_line = [l for l in lines if "RANK 1" in l][0]
        self.assertIn("item01", rank1_line)
        idx_item01 = result.index("[item01]")
        idx_item04 = result.index("[item04]")
        self.assertLess(idx_item01, idx_item04)

    def test_execution_order_line_present(self):
        """Output should include 'Recommended execution order' line."""
        data = (
            "item01|patch|EFFORT:1|IMPACT:5|DEPENDENCY:none\n"
            "item02|train|EFFORT:3|IMPACT:2|DEPENDENCY:none"
        )
        result = run_tool("remediation_planner", data)
        self.assertIn("Recommended execution order", result)


class TestStaticReferences(unittest.TestCase):
    """Tests for exec_reference and notification_reference — static output."""

    def test_exec_reference_contains_all_sections(self):
        """exec_reference must contain all 6 standard report sections."""
        result = run_tool("exec_reference", "ignored input")
        self.assertIn("EXECUTIVE SUMMARY", result)
        self.assertIn("TIMELINE", result)
        self.assertIn("TECHNICAL ANALYSIS", result)
        self.assertIn("BUSINESS IMPACT", result)
        self.assertIn("RECOMMENDATIONS", result)
        self.assertIn("LESSONS LEARNED", result)

    def test_exec_reference_ignores_input(self):
        """exec_reference output should be identical regardless of input."""
        r1 = run_tool("exec_reference", "anything")
        r2 = run_tool("exec_reference", "something else entirely")
        self.assertEqual(r1, r2)

    def test_notification_reference_contains_gdpr_72h(self):
        """notification_reference must contain GDPR and the 72-hour deadline."""
        result = run_tool("notification_reference", "ignored input")
        self.assertIn("GDPR", result)
        self.assertIn("72", result)

    def test_notification_reference_contains_all_regulations(self):
        """notification_reference must contain GDPR, HIPAA, PCI DSS, and CCPA."""
        result = run_tool("notification_reference", "")
        self.assertIn("GDPR", result)
        self.assertIn("HIPAA", result)
        self.assertIn("PCI DSS", result)
        self.assertIn("CCPA", result)

    def test_notification_reference_ignores_input(self):
        """notification_reference output should be identical regardless of input."""
        r1 = run_tool("notification_reference", "EU breach scenario")
        r2 = run_tool("notification_reference", "US HIPAA scenario")
        self.assertEqual(r1, r2)


if __name__ == "__main__":
    unittest.main()
