"""test_tools_stage4.py — AEGIS Stage 4 unit tests

Tests for the 8 new dynamic tool functions added in Stage 4:
  vuln_prioritizer, surface_analyzer, sast_analyzer, intel_correlator,
  metrics_calculator, compliance_mapper, sla_tracker, dashboard_filter

40 tests total across 8 test classes.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aegis.utils.tools import (
    vuln_prioritizer,
    surface_analyzer,
    sast_analyzer,
    intel_correlator,
    metrics_calculator,
    compliance_mapper,
    sla_tracker,
    dashboard_filter,
)

# ---------------------------------------------------------------------------
# Shared test data constants (mirror challenge_data from case JSON files)
# ---------------------------------------------------------------------------

CASE22_DATA = (
    "CVE-2021-44228|10.0|critical|yes|yes|yes\n"
    "CVE-2022-30190|7.8|high|no|yes|yes\n"
    "CVE-2023-1234|6.5|medium|yes|no|yes\n"
    "CVE-2021-34527|8.8|high|no|yes|no"
)

CASE24_DATA = (
    "ssh|22|tcp|yes|yes|remote_management\n"
    "telnet|23|tcp|yes|no|remote_management\n"
    "ftp|21|tcp|yes|no|file_transfer\n"
    "https|443|tcp|yes|yes|web_service\n"
    "rdp|3389|tcp|yes|no|remote_management\n"
    "smb|445|tcp|yes|no|file_sharing"
)

CASE25_DATA = (
    "auth.py|45|CWE-89|critical|SQL injection via unsanitized user input in login query\n"
    "config.py|12|CWE-798|high|Hardcoded credential: API_KEY set to production secret value\n"
    "upload.py|78|CWE-22|high|Path traversal: filename not validated before file write operation\n"
    "session.py|33|CWE-384|medium|Session fixation: session ID not regenerated after successful login\n"
    "logger.py|91|CWE-532|low|Sensitive data in logs: password field written to access.log"
)

CASE26_DATA = (
    "CVE-2023-5678|7.2|yes|yes|yes\n"
    "CVE-2022-9876|8.5|no|yes|no\n"
    "CVE-2023-1111|6.8|no|no|yes\n"
    "CVE-2021-0001|9.0|no|no|no"
)

CASE27_DATA = (
    "INC-001|2026-03-01T00:00:00|2026-03-22T12:00:00|2026-03-24T12:00:00\n"
    "INC-002|2026-03-15T10:00:00|2026-03-15T12:00:00|2026-03-16T12:00:00\n"
    "INC-003|2026-03-28T00:00:00|2026-03-30T00:00:00|2026-04-01T12:00:00"
)

CASE28_DATA = (
    "ID-AM-01|IDENTIFY|yes\n"
    "ID-RA-01|IDENTIFY|yes\n"
    "PR-AC-01|PROTECT|yes\n"
    "PR-DS-01|PROTECT|yes\n"
    "PR-IP-01|PROTECT|yes\n"
    "DE-AE-01|DETECT|yes\n"
    "DE-CM-01|DETECT|yes\n"
    "RS-RP-01|RESPOND|yes\n"
    "RS-CO-01|RESPOND|yes\n"
    "RC-RP-01|RECOVER|no\n"
    "RC-RP-02|RECOVER|no\n"
    "RC-IM-01|RECOVER|no\n"
    "RC-IM-02|RECOVER|no\n"
    "RC-CO-01|RECOVER|no\n"
    "RC-CO-02|RECOVER|yes"
)

CASE29_DATA = (
    "TKT-001|critical|2026-04-01T08:00:00|2026-04-01T10:00:00|4\n"
    "TKT-002|high|2026-04-02T09:00:00|2026-04-03T11:00:00|24\n"
    "TKT-003|medium|2026-04-03T14:00:00|2026-04-07T14:00:00|72\n"
    "TKT-004|critical|2026-04-05T22:00:00|2026-04-06T06:00:00|4\n"
    "TKT-005|high|2026-04-08T10:00:00|2026-04-09T06:00:00|24\n"
    "TKT-006|low|2026-04-10T11:00:00|2026-04-20T11:00:00|120"
)

CASE31_DATA = (
    "mean_time_to_detect|189 hours\n"
    "overall_risk_reduction|23 percent\n"
    "patch_compliance_rate|78 percent\n"
    "total_alerts_processed|1247\n"
    "critical_vulnerabilities_open|12\n"
    "average_scan_cycle_time|14 days\n"
    "sla_adherence_rate|33 percent\n"
    "firewall_rules_reviewed|847"
)


# ---------------------------------------------------------------------------
# TestVulnPrioritizer
# ---------------------------------------------------------------------------

class TestVulnPrioritizer(unittest.TestCase):

    def test_top_priority_is_log4shell(self):
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("[RANK 1] CVE-2021-44228", result)

    def test_log4shell_score_17(self):
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("17.0", result)

    def test_lowest_priority_is_cve_2023_1234(self):
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("[RANK 4] CVE-2023-1234", result)

    def test_rank_order_correct(self):
        result = vuln_prioritizer(CASE22_DATA)
        pos1 = result.index("[RANK 1]")
        pos2 = result.index("[RANK 2]")
        pos3 = result.index("[RANK 3]")
        pos4 = result.index("[RANK 4]")
        self.assertLess(pos1, pos2)
        self.assertLess(pos2, pos3)
        self.assertLess(pos3, pos4)

    def test_no_internet_no_bonus(self):
        # CVE-2022-30190: 7.8 + 2(high) + 2(exploit) + 0(no internet) = 11.8
        result = vuln_prioritizer(CASE22_DATA)
        self.assertIn("11.8", result)


# ---------------------------------------------------------------------------
# TestSurfaceAnalyzer
# ---------------------------------------------------------------------------

class TestSurfaceAnalyzer(unittest.TestCase):

    def test_four_reduce_services(self):
        result = surface_analyzer(CASE24_DATA)
        self.assertIn("4 services flagged", result)

    def test_reduce_flags_correct(self):
        result = surface_analyzer(CASE24_DATA)
        self.assertIn("[REDUCE] telnet", result)
        self.assertIn("[REDUCE] ftp", result)
        self.assertIn("[REDUCE] rdp", result)
        self.assertIn("[REDUCE] smb", result)

    def test_ok_flags_correct(self):
        result = surface_analyzer(CASE24_DATA)
        self.assertIn("[OK] ssh", result)
        self.assertIn("[OK] https", result)

    def test_reduce_before_ok_in_output(self):
        result = surface_analyzer(CASE24_DATA)
        first_reduce = result.index("[REDUCE]")
        first_ok = result.index("[OK]")
        self.assertLess(first_reduce, first_ok)

    def test_required_yes_never_reduce(self):
        data = "webapp|443|tcp|yes|yes|web_service"
        result = surface_analyzer(data)
        self.assertIn("[OK]", result)
        # Check no service is *tagged* [REDUCE] — summary text may mention it
        self.assertNotIn("\n[REDUCE]", result)


# ---------------------------------------------------------------------------
# TestSastAnalyzer
# ---------------------------------------------------------------------------

class TestSastAnalyzer(unittest.TestCase):

    def test_top_finding_is_cwe89(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertIn("Top finding: CWE-89", result)

    def test_critical_before_high(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertLess(result.index("[CRITICAL]"), result.index("[HIGH]"))

    def test_high_before_medium(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertLess(result.index("[HIGH]"), result.index("[MEDIUM]"))

    def test_medium_before_low(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertLess(result.index("[MEDIUM]"), result.index("[LOW]"))

    def test_cwe_name_resolved(self):
        result = sast_analyzer(CASE25_DATA)
        self.assertIn("SQL Injection", result)
        self.assertIn("Use of Hard-coded Credentials", result)


# ---------------------------------------------------------------------------
# TestIntelCorrelator
# ---------------------------------------------------------------------------

class TestIntelCorrelator(unittest.TestCase):

    def test_exploited_wild_gets_immediate(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[IMMEDIATE] CVE-2023-5678", result)

    def test_poc_only_gets_elevated(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[ELEVATED] CVE-2022-9876", result)

    def test_apt_only_gets_monitor(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[MONITOR] CVE-2023-1111", result)

    def test_high_cvss_no_intel_gets_routine(self):
        result = intel_correlator(CASE26_DATA)
        self.assertIn("[ROUTINE] CVE-2021-0001", result)

    def test_immediate_before_routine_in_output(self):
        result = intel_correlator(CASE26_DATA)
        self.assertLess(
            result.index("[IMMEDIATE]"),
            result.index("[ROUTINE]")
        )


# ---------------------------------------------------------------------------
# TestMetricsCalculator
# ---------------------------------------------------------------------------

class TestMetricsCalculator(unittest.TestCase):

    def test_mttd_189(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("189 hours", result)

    def test_mttr_44(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("44 hours", result)

    def test_inc001_mttd_516(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("516.00h", result)

    def test_inc002_mttd_2(self):
        result = metrics_calculator(CASE27_DATA)
        self.assertIn("2.00h", result)

    def test_single_incident_mttd(self):
        # MTTD = Jan1->Jan3 = 48h; MTTR = Jan3->Jan4 = 24h
        data = "INC-X|2026-01-01T00:00:00|2026-01-03T00:00:00|2026-01-04T00:00:00"
        result = metrics_calculator(data)
        self.assertIn("48 hours", result)


# ---------------------------------------------------------------------------
# TestComplianceMapper
# ---------------------------------------------------------------------------

class TestComplianceMapper(unittest.TestCase):

    def test_recover_lowest(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("17%", result)

    def test_recover_is_top_gap(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("Top priority gap: RECOVER", result)

    def test_recover_critical_gap_label(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("[CRITICAL GAP]", result)
        self.assertIn("RECOVER", result)

    def test_full_compliance_functions_present(self):
        result = compliance_mapper(CASE28_DATA)
        self.assertIn("100%", result)

    def test_recover_appears_before_identify(self):
        result = compliance_mapper(CASE28_DATA)
        pos_recover = result.index("RECOVER")
        pos_identify = result.index("IDENTIFY")
        self.assertLess(pos_recover, pos_identify)


# ---------------------------------------------------------------------------
# TestSlaTracker
# ---------------------------------------------------------------------------

class TestSlaTracker(unittest.TestCase):

    def test_adherence_rate_33(self):
        result = sla_tracker(CASE29_DATA)
        self.assertIn("33%", result)

    def test_tkt001_met(self):
        result = sla_tracker(CASE29_DATA)
        idx = result.index("TKT-001")
        snippet = result[idx:idx+70]
        self.assertIn("[MET]", snippet)

    def test_tkt004_breached(self):
        result = sla_tracker(CASE29_DATA)
        idx = result.index("TKT-004")
        snippet = result[idx:idx+70]
        self.assertIn("[BREACHED]", snippet)

    def test_tkt005_met(self):
        result = sla_tracker(CASE29_DATA)
        idx = result.index("TKT-005")
        snippet = result[idx:idx+70]
        self.assertIn("[MET]", snippet)

    def test_exact_sla_is_met(self):
        # elapsed == sla_hours exactly -> MET (inclusive boundary)
        data = "TKT-X|high|2026-01-01T00:00:00|2026-01-02T00:00:00|24"
        result = sla_tracker(data)
        self.assertIn("[MET]", result)


# ---------------------------------------------------------------------------
# TestDashboardFilter
# ---------------------------------------------------------------------------

class TestDashboardFilter(unittest.TestCase):

    def test_four_executive_metrics(self):
        result = dashboard_filter(CASE31_DATA)
        self.assertIn("Executive dashboard:  4 metrics", result)

    def test_executive_metrics_correct(self):
        result = dashboard_filter(CASE31_DATA)
        self.assertIn("[EXECUTIVE] overall_risk_reduction", result)
        self.assertIn("[EXECUTIVE] patch_compliance_rate", result)
        self.assertIn("[EXECUTIVE] critical_vulnerabilities_open", result)
        self.assertIn("[EXECUTIVE] sla_adherence_rate", result)

    def test_operational_metrics_correct(self):
        result = dashboard_filter(CASE31_DATA)
        self.assertIn("[OPERATIONAL] mean_time_to_detect", result)
        self.assertIn("[OPERATIONAL] total_alerts_processed", result)

    def test_executive_before_operational_in_output(self):
        result = dashboard_filter(CASE31_DATA)
        first_exec = result.index("[EXECUTIVE]")
        first_oper = result.index("[OPERATIONAL]")
        self.assertLess(first_exec, first_oper)

    def test_single_executive_metric(self):
        data = "overall_risk_reduction|15 percent"
        result = dashboard_filter(data)
        self.assertIn("[EXECUTIVE]", result)
        self.assertNotIn("[OPERATIONAL]", result)


if __name__ == "__main__":
    unittest.main()
