#!/usr/bin/env python3
"""
Day 20: Interactive Dashboard Test Script
Testet alle Funktionen des Interactive Dashboard Systems.
"""

import requests
import time
import json
from typing import Dict, Any


class DashboardTester:
    """Testet alle Interactive Dashboard Endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8008"):
        self.base_url = base_url
        self.session_id = f"test_session_{int(time.time())}"
        self.results = []
        
    def log(self, test_name: str, success: bool, message: str):
        """Log test result."""
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    def test_health(self) -> bool:
        """Test health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log("Health Check", True, f"Server is healthy: {data['status']}")
                return True
            else:
                self.log("Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Health Check", False, str(e))
            return False
    
    def test_list_sessions(self) -> bool:
        """Test sessions listing."""
        try:
            response = requests.get(f"{self.base_url}/api/sessions")
            if response.status_code == 200:
                data = response.json()
                self.log("List Sessions", True, f"Found {data['total_sessions']} sessions")
                return True
            else:
                self.log("List Sessions", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("List Sessions", False, str(e))
            return False
    
    def test_start_session(self) -> bool:
        """Test starting a new heist session."""
        try:
            payload = {
                "session_id": self.session_id,
                "agents": ["planner", "hacker", "safecracker"],
                "config": {"test_mode": True}
            }
            response = requests.post(
                f"{self.base_url}/api/heist/start",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log("Start Session", True, f"Session {self.session_id} started")
                    return True
                else:
                    self.log("Start Session", False, data.get("error", "Unknown error"))
                    return False
            else:
                self.log("Start Session", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Start Session", False, str(e))
            return False
    
    def test_get_session_status(self) -> bool:
        """Test getting session status."""
        try:
            response = requests.get(f"{self.base_url}/api/heist/{self.session_id}/status")
            if response.status_code == 200:
                data = response.json()
                self.log("Get Session Status", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log("Get Session Status", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Get Session Status", False, str(e))
            return False
    
    def test_send_command(self) -> bool:
        """Test sending command to agent."""
        try:
            payload = {
                "agent": "hacker",
                "command": "Disable security camera in vault area"
            }
            response = requests.post(
                f"{self.base_url}/api/heist/{self.session_id}/command",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log("Send Command", True, f"Command sent to {payload['agent']}")
                    return True
                else:
                    self.log("Send Command", False, data.get("error", "Unknown error"))
                    return False
            else:
                self.log("Send Command", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Send Command", False, str(e))
            return False
    
    def test_get_pending_commands(self) -> bool:
        """Test getting pending commands."""
        try:
            response = requests.get(f"{self.base_url}/api/heist/{self.session_id}/commands")
            if response.status_code == 200:
                data = response.json()
                self.log("Get Pending Commands", True, f"Found {data['count']} pending commands")
                return True
            else:
                self.log("Get Pending Commands", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Get Pending Commands", False, str(e))
            return False
    
    def test_pause_session(self) -> bool:
        """Test pausing session."""
        try:
            response = requests.post(f"{self.base_url}/api/heist/{self.session_id}/pause")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log("Pause Session", True, "Session paused successfully")
                    return True
                else:
                    self.log("Pause Session", False, data.get("error", "Unknown error"))
                    return False
            else:
                self.log("Pause Session", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Pause Session", False, str(e))
            return False
    
    def test_resume_session(self) -> bool:
        """Test resuming session."""
        try:
            response = requests.post(f"{self.base_url}/api/heist/{self.session_id}/resume")
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log("Resume Session", True, "Session resumed successfully")
                    return True
                else:
                    self.log("Resume Session", False, data.get("error", "Unknown error"))
                    return False
            else:
                self.log("Resume Session", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Resume Session", False, str(e))
            return False
    
    def test_get_active_heists(self) -> bool:
        """Test getting all active heists."""
        try:
            response = requests.get(f"{self.base_url}/api/heist/active")
            if response.status_code == 200:
                data = response.json()
                self.log("Get Active Heists", True, f"Found {data['count']} active heists")
                return True
            else:
                self.log("Get Active Heists", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Get Active Heists", False, str(e))
            return False
    
    def test_detect_mole(self) -> bool:
        """Test mole detection."""
        try:
            payload = {"agent": "safecracker"}
            response = requests.post(
                f"{self.base_url}/api/heist/{self.session_id}/detect-mole",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log("Detect Mole", True, f"Marked {payload['agent']} as detected mole")
                    return True
                else:
                    self.log("Detect Mole", False, data.get("error", "Unknown error"))
                    return False
            else:
                self.log("Detect Mole", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Detect Mole", False, str(e))
            return False
    
    def test_get_mole_status(self) -> bool:
        """Test getting mole status."""
        try:
            response = requests.get(f"{self.base_url}/api/heist/{self.session_id}/mole-status")
            if response.status_code == 200:
                data = response.json()
                self.log("Get Mole Status", True, f"Detected: {data.get('detected_mole')}")
                return True
            else:
                self.log("Get Mole Status", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log("Get Mole Status", False, str(e))
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print("=" * 80)
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print("=" * 80)
        print("🧪 Day 20: Interactive Dashboard Test Suite")
        print("=" * 80)
        print()
        
        # Basic connectivity
        if not self.test_health():
            print("\n❌ Server is not responding. Please start the server first.")
            print("   Run: python3 day_20/interactive_dashboard_server.py")
            return
        
        print()
        
        # Session management
        self.test_list_sessions()
        self.test_start_session()
        self.test_get_session_status()
        
        print()
        
        # Command injection
        self.test_send_command()
        time.sleep(0.5)  # Give server time to process
        self.test_get_pending_commands()
        
        print()
        
        # Pause/Resume control
        self.test_pause_session()
        time.sleep(0.5)
        self.test_resume_session()
        
        print()
        
        # Active heists
        self.test_get_active_heists()
        
        print()
        
        # Mole detection (Tag 21 feature)
        self.test_detect_mole()
        self.test_get_mole_status()
        
        print()
        
        # Print summary
        self.print_summary()


def main():
    """Run all tests."""
    tester = DashboardTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
