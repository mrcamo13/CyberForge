"""test_tools_stage3.py — AEGIS Stage 3 unit tests

Tests for all 7 new dynamic tool functions introduced in Stage 3.
All tests are deterministic (no I/O, no randomness).
"""

import unittest

from aegis.utils.tools import (
    siem_correlator,
    log_classifier,
    hunt_analyzer,
    mem_analyzer,
    disk_analyzer,
    containment_advisor,
    timeline_builder,
    coc_reference,
)

# ---------------------------------------------------------------------------
# Challenge data for case-level tests
# ---------------------------------------------------------------------------

CASE14_DATA = (
    "R001|CONDITION:event_type=auth_failure AND source=external|SEVERITY:high\n"
    "R002|CONDITION:event_type=auth_success AND source=external AND details=root|SEVERITY:critical\n"
    "R003|CONDITION:event_type=process_create AND details=powershell|SEVERITY:medium\n"
    "R004|CONDITION:event_type=network_connect AND details=port=4444|SEVERITY:high"
    "|||"
    "2026-04-05T22:14:01|firewall|auth_failure|source=external user=admin\n"
    "2026-04-05T22:14:03|syslog|auth_failure|source=external user=root\n"
    "2026-04-05T22:14:07|syslog|auth_success|source=external user=root details=root\n"
    "2026-04-05T22:15:12|sysmon|process_create|details=powershell -enc SQBFAFgA\n"
    "2026-04-05T22:16:30|firewall|network_connect|details=dst=185.220.101.45 port=4444\n"
    "2026-04-05T22:18:00|syslog|auth_failure|source=internal user=backup"
)

CASE15_DATA = (
    "failed login attempt for user administrator\n"
    "outbound connection to 185.220.101.45 port 4444\n"
    "DNS query for nightwire-c2.xyz\n"
    "new scheduled task created: WindowsUpdate\n"
    "powershell.exe spawned by wscript.exe\n"
    "USB device inserted: SanDisk 64GB"
)

CASE16_DATA = (
    "NIGHTWIRE is using living-off-the-land techniques to avoid detection"
    "|||"
    "process:powershell.exe -enc SQBFAFgA\n"
    "process:certutil.exe -decode payload.b64\n"
    "process:svchost.exe -k netsvcs\n"
    "network:10.0.0.15 to 185.220.101.45:443\n"
    "file:/tmp/update.sh created\n"
    "registry:HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run modified\n"
    "process:explorer.exe parent=userinit.exe"
)

CASE17_DATA = (
    "PID:4 name:System base:0x00000000 size:8192 permissions:r-- path:[kernel]\n"
    "PID:892 name:svchost base:0x7FFE0000 size:4096 permissions:r-x path:C:\\Windows\\System32\\svchost.exe\n"
    "PID:1337 name:update base:0xFF001000 size:65536 permissions:rwx path:[anon]\n"
    "PID:2048 name:explorer base:0x00400000 size:8192 permissions:r-x path:C:\\Windows\\explorer.exe\n"
    "PID:3001 name:powershell base:0x10000000 size:4096 permissions:r-x path:C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\n"
    "PID:3999 name:svchost base:0x00200000 size:102400 permissions:r-x path:C:\\Windows\\System32\\svchost.exe"
)

CASE18_DATA = (
    "nightwire.exe|45056|2026-03-20T14:00:00|2026-03-20T14:00:00|2026-04-05T22:15:00|deleted:yes|C:\\Users\\Public\\nightwire.exe\n"
    "update.bat|512|2026-04-05T22:14:30|2026-04-05T22:14:30|2026-04-05T22:14:30|deleted:no|C:\\Windows\\Temp\\update.bat\n"
    "svchost.exe|28672|2026-03-15T09:00:00|2026-03-15T09:00:00|2026-04-05T22:16:00|deleted:no|C:\\Windows\\System32\\svchost.exe\n"
    "mimikatz.exe|1245184|2026-04-05T22:20:00|2026-03-01T00:00:00|2026-04-05T22:20:00|deleted:yes|C:\\Users\\Public\\Downloads\\mimikatz.exe\n"
    "config.sys|128|2021-01-01T00:00:00|2021-01-01T00:00:00|2026-04-05T22:10:00|deleted:no|C:\\Windows\\System32\\config.sys\n"
    "payload.b64|8192|2026-04-05T22:14:00|2026-04-05T22:14:00|2026-04-05T22:14:00|deleted:yes|C:\\Temp\\payload.b64"
)

CASE20_DATA = (
    "asset:domain_controller|threat:critical|dwell:42|data_sensitivity:restricted|attribution:known"
)

CASE21_DATA = (
    "2026-03-20T14:00:00|disk|nightwire.exe dropped to C:\\Users\\Public\n"
    "2026-03-20T14:02:00|registry|HKLM\\...\\Run key modified -- persistence established\n"
    "2026-04-05T22:14:07|syslog|auth_success -- external root login\n"
    "2026-04-05T22:15:12|sysmon|powershell -enc SQBFAFgA executed\n"
    "2026-04-05T22:16:30|firewall|outbound connection to 185.220.101.45:4444\n"
    "2026-04-05T22:20:00|disk|mimikatz.exe executed then deleted\n"
    "2026-04-11T03:15:00|syslog|NexusCorp attacker detected -- separate incident triggered IR\n"
    "2026-04-11T03:20:00|ir_team|NIGHTWIRE artifacts identified during NexusCorp investigation\n"
    "2026-04-11T03:45:00|ir_team|DC-01 network isolated -- NIGHTWIRE C2 channel blocked\n"
    "2026-04-11T04:30:00|ir_team|forensic imaging of DC-01 initiated\n"
    "2026-04-12T09:00:00|ir_team|NIGHTWIRE investigation formally opened -- Project MERIDIAN"
)


# ---------------------------------------------------------------------------
# TestSiemCorrelator
# ---------------------------------------------------------------------------

class TestSiemCorrelator(unittest.TestCase):

    def test_critical_alert_fires(self):
        result = siem_correlator(CASE14_DATA)
        self.assertIn("[ALERT — CRITICAL] R002", result)

    def test_high_alert_fires_twice(self):
        result = siem_correlator(CASE14_DATA)
        self.assertEqual(result.count("[ALERT — HIGH] R001"), 2)

    def test_no_alert_for_internal_source(self):
        result = siem_correlator(CASE14_DATA)
        self.assertIn("No alert fired on: 2026-04-05T22:18:00", result)

    def test_highest_severity_in_summary(self):
        result = siem_correlator(CASE14_DATA)
        self.assertIn("Highest severity: CRITICAL", result)

    def test_all_matching_rules_fire(self):
        # Two events, each matching a different rule — both alerts appear
        data = (
            "R003|CONDITION:event_type=process_create AND details=powershell|SEVERITY:medium\n"
            "R004|CONDITION:event_type=network_connect AND details=port=4444|SEVERITY:high"
            "|||"
            "2026-01-01T00:00:01|host|process_create|details=powershell -enc AAAA\n"
            "2026-01-01T00:00:02|host|network_connect|details=dst=1.2.3.4 port=4444"
        )
        result = siem_correlator(data)
        self.assertIn("[ALERT — MEDIUM] R003", result)
        self.assertIn("[ALERT — HIGH] R004", result)


# ---------------------------------------------------------------------------
# TestLogClassifier
# ---------------------------------------------------------------------------

class TestLogClassifier(unittest.TestCase):

    def test_failed_login_maps_to_security_log(self):
        result = log_classifier("failed login attempt for user admin")
        self.assertIn("Event 4625", result)

    def test_dns_query_maps_to_dns_logs(self):
        result = log_classifier("DNS query for malicious-domain.com")
        self.assertIn("DNS server logs", result)

    def test_scheduled_task_maps_to_event_4698(self):
        result = log_classifier("new scheduled task created: WindowsUpdate")
        self.assertIn("Event 4698", result)

    def test_usb_maps_to_event_6416(self):
        result = log_classifier("USB device inserted: SanDisk 64GB")
        self.assertIn("Event 6416", result)

    def test_no_match_returns_unknown(self):
        result = log_classifier("quantum entanglement event observed")
        self.assertIn("Unknown", result)


# ---------------------------------------------------------------------------
# TestHuntAnalyzer
# ---------------------------------------------------------------------------

class TestHuntAnalyzer(unittest.TestCase):

    def test_powershell_enc_is_supports(self):
        result = hunt_analyzer("LOLBAS hypothesis|||process:powershell.exe -enc AAAA")
        self.assertIn("[SUPPORTS]", result)

    def test_certutil_decode_is_supports(self):
        result = hunt_analyzer("LOLBAS hypothesis|||process:certutil.exe -decode file.b64")
        self.assertIn("[SUPPORTS]", result)

    def test_svchost_normal_is_refutes(self):
        result = hunt_analyzer("LOLBAS hypothesis|||process:svchost.exe -k netsvcs")
        self.assertIn("[REFUTES]", result)

    def test_confidence_60_percent_case16(self):
        result = hunt_analyzer(CASE16_DATA)
        self.assertIn("60%", result)

    def test_confidence_zero_all_neutral(self):
        result = hunt_analyzer(
            "LOLBAS hypothesis|||network:192.168.1.1\nfile:document.docx"
        )
        self.assertTrue("0%" in result or "INSUFFICIENT EVIDENCE" in result)

    def test_registry_run_is_supports(self):
        result = hunt_analyzer(
            "LOLBAS hypothesis|||registry:HKLM\\CurrentVersion\\Run modified"
        )
        self.assertIn("[SUPPORTS]", result)


# ---------------------------------------------------------------------------
# TestMemAnalyzer
# ---------------------------------------------------------------------------

class TestMemAnalyzer(unittest.TestCase):

    def test_rwx_anon_is_suspicious(self):
        result = mem_analyzer(
            "PID:1337 name:update base:0xFF001000 size:65536 permissions:rwx path:[anon]"
        )
        self.assertIn("[SUSPICIOUS]", result)

    def test_large_svchost_is_anomaly(self):
        result = mem_analyzer(
            "PID:3999 name:svchost base:0x00200000 size:102400 "
            "permissions:r-x path:C:\\Windows\\System32\\svchost.exe"
        )
        self.assertIn("[ANOMALY]", result)

    def test_normal_process_is_ok(self):
        result = mem_analyzer(
            "PID:2048 name:explorer base:0x00400000 size:8192 "
            "permissions:r-x path:C:\\Windows\\explorer.exe"
        )
        self.assertIn("[OK]", result)

    def test_malicious_name_is_malicious(self):
        result = mem_analyzer(
            "PID:9999 name:mimikatz base:0x10000000 size:1024 "
            "permissions:r-x path:C:\\Temp\\mimikatz.exe"
        )
        self.assertIn("[MALICIOUS]", result)

    def test_case17_finds_pid_1337(self):
        result = mem_analyzer(CASE17_DATA)
        self.assertIn("PID 1337", result)
        self.assertIn("[SUSPICIOUS]", result)


# ---------------------------------------------------------------------------
# TestDiskAnalyzer
# ---------------------------------------------------------------------------

class TestDiskAnalyzer(unittest.TestCase):

    def test_mimikatz_is_malicious(self):
        result = disk_analyzer(
            "mimikatz.exe|1245184|2026-04-05T22:20:00|2026-03-01T00:00:00"
            "|2026-04-05T22:20:00|deleted:yes|C:\\Users\\Public\\Downloads\\mimikatz.exe"
        )
        self.assertIn("[MALICIOUS]", result)

    def test_timestomped_detected(self):
        result = disk_analyzer(
            "tool.exe|1024|2026-04-05T10:00:00|2026-04-01T00:00:00"
            "|2026-04-05T10:00:00|deleted:no|C:\\Windows\\tool.exe"
        )
        self.assertIn("[TIMESTOMPED]", result)

    def test_deleted_file_flagged(self):
        result = disk_analyzer(
            "payload.bin|8192|2026-04-05T22:14:00|2026-04-05T22:14:00"
            "|2026-04-05T22:14:00|deleted:yes|C:\\Temp\\payload.bin"
        )
        self.assertIn("[DELETED]", result)

    def test_suspicious_path_flagged(self):
        result = disk_analyzer(
            "script.sh|512|2026-04-05T22:14:00|2026-04-05T22:14:00"
            "|2026-04-05T22:14:00|deleted:no|/tmp/script.sh"
        )
        self.assertIn("[SUSPICIOUS]", result)

    def test_malicious_takes_priority_over_deleted(self):
        # Two entries: one non-malicious deleted file, one malicious file.
        # The malicious file must appear before the deleted one in sorted output.
        data = (
            "payload.bin|512|2026-04-05T10:00:00|2026-04-05T10:00:00"
            "|2026-04-05T10:00:00|deleted:yes|C:\\Temp\\payload.bin\n"
            "mimikatz.exe|512|2026-04-05T10:00:00|2026-04-05T10:00:00"
            "|2026-04-05T10:00:00|deleted:no|C:\\Temp\\mimikatz.exe"
        )
        result = disk_analyzer(data)
        self.assertIn("[MALICIOUS]", result)
        self.assertIn("[DELETED]", result)
        self.assertLess(result.index("[MALICIOUS]"), result.index("[DELETED]"))

    def test_case18_summary_line(self):
        result = disk_analyzer(CASE18_DATA)
        self.assertIn("1 MALICIOUS", result)
        self.assertIn("2 DELETED", result)
        self.assertIn("1 SUSPICIOUS", result)


# ---------------------------------------------------------------------------
# TestContainmentAdvisor
# ---------------------------------------------------------------------------

class TestContainmentAdvisor(unittest.TestCase):

    def test_case20_recommends_network_isolation(self):
        result = containment_advisor(CASE20_DATA)
        self.assertIn("RECOMMENDATION: Network Isolation", result)

    def test_full_isolation_high_tip_risk_when_known_long_dwell(self):
        result = containment_advisor(CASE20_DATA)
        # Full Isolation is Option 1 — check its tip-off risk line
        full_block = result.split("OPTION 2:")[0]  # everything before option 2
        self.assertIn("Tip-off risk:   5/5", full_block)

    def test_full_isolation_lower_tip_risk_when_short_dwell(self):
        data = "asset:workstation|threat:high|dwell:5|data_sensitivity:internal|attribution:unknown"
        result = containment_advisor(data)
        full_block = result.split("OPTION 2:")[0]
        self.assertIn("Tip-off risk:   3/5", full_block)

    def test_monitoring_only_net_score_is_1(self):
        result = containment_advisor(CASE20_DATA)
        mon_block = result.split("OPTION 3:")[1].split("OPTION 4:")[0]
        self.assertIn("Net score:      1", mon_block)


# ---------------------------------------------------------------------------
# TestTimelineBuilder
# ---------------------------------------------------------------------------

class TestTimelineBuilder(unittest.TestCase):

    def test_events_sorted_chronologically(self):
        data = (
            "2026-04-05T22:16:30|firewall|C2 beacon\n"
            "2026-03-20T14:00:00|disk|file dropped"
        )
        result = timeline_builder(data)
        self.assertLess(result.index("2026-03-20"), result.index("2026-04-05"))

    def test_gap_over_1_hour_annotated(self):
        data = (
            "2026-04-05T22:16:30|firewall|C2 beacon\n"
            "2026-03-20T14:00:00|disk|file dropped"
        )
        result = timeline_builder(data)
        self.assertIn("[GAP:", result)

    def test_no_gap_for_events_within_1_hour(self):
        data = (
            "2026-04-05T22:14:00|syslog|event A\n"
            "2026-04-05T22:16:00|sysmon|event B"
        )
        result = timeline_builder(data)
        self.assertNotIn("[GAP:", result)

    def test_deleted_keyword_labels_eradication(self):
        result = timeline_builder(
            "2026-04-05T22:20:00|disk|mimikatz.exe executed then deleted"
        )
        self.assertIn("[Eradication]", result)

    def test_isolated_keyword_labels_containment(self):
        result = timeline_builder(
            "2026-04-11T03:45:00|ir_team|DC-01 network isolated"
        )
        self.assertIn("[Containment]", result)

    def test_case21_gap_annotation_392h(self):
        result = timeline_builder(CASE21_DATA)
        self.assertIn("392h 12m", result)


# ---------------------------------------------------------------------------
# TestCocReference
# ---------------------------------------------------------------------------

class TestCocReference(unittest.TestCase):

    def test_returns_hash_step(self):
        result = coc_reference()
        self.assertIn("STEP 2: HASH THE EVIDENCE", result)

    def test_returns_common_errors(self):
        result = coc_reference()
        self.assertIn("COMMON ERRORS TO AVOID", result)

    def test_ignores_input(self):
        result_empty = coc_reference("")
        result_any = coc_reference("some challenge data string here")
        self.assertEqual(result_empty, result_any)


if __name__ == "__main__":
    unittest.main()
