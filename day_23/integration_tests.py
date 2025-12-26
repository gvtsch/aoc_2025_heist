"""
Day 23: Integration Tests
End-to-end tests for the complete heist system.
"""

import unittest
import sys
import os
import time
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from day_16.integrated_system import IntegratedSystem
from day_17.session_manager import SessionManager
from day_21.heist_game import HeistGame
from day_22.saboteur_detector import SaboteurDetector


class TestIntegratedSystem(unittest.TestCase):
    """Test complete system integration."""

    @classmethod
    def setUpClass(cls):
        """Setup test environment."""
        cls.config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "day_15",
            "agents_config.yaml"
        )
        cls.db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "test_heist.db"
        )

    def setUp(self):
        """Initialize system for each test."""
        self.system = IntegratedSystem(self.config_path)

    def test_system_initialization(self):
        """Test that system initializes correctly."""
        self.assertIsNotNone(self.system)
        self.assertEqual(len(self.system.agents), 4)
        self.assertIn('planner', self.system.agents)
        self.assertIn('hacker', self.system.agents)
        self.assertIn('safecracker', self.system.agents)
        self.assertIn('mole', self.system.agents)

    def test_conversation_flow(self):
        """Test that conversation runs without errors."""
        try:
            self.system.run_conversation(num_turns=2)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Conversation failed: {e}")

    def test_database_persistence(self):
        """Test that messages are persisted to database."""
        session_id = self.system.session_id
        self.system.run_conversation(num_turns=2)

        # Check database
        manager = SessionManager(self.system.db_manager.db_path)
        sessions = manager.list_sessions()

        self.assertGreater(len(sessions), 0)

        # Verify session exists
        session_ids = [s.session_id for s in sessions]
        self.assertIn(session_id, session_ids)

    def test_session_analytics(self):
        """Test that session analytics work correctly."""
        self.system.run_conversation(num_turns=2)

        manager = SessionManager(self.system.db_manager.db_path)
        sessions = manager.list_sessions()

        self.assertGreater(len(sessions), 0)

        # Get details
        details = manager.get_session_details(sessions[0].session_id)

        self.assertIn('messages', details)
        self.assertIn('agent_stats', details)
        self.assertGreater(len(details['messages']), 0)


class TestHeistGame(unittest.TestCase):
    """Test heist game mechanics."""

    @classmethod
    def setUpClass(cls):
        """Setup test environment."""
        cls.config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "day_15",
            "agents_config.yaml"
        )

    def test_random_mole_selection(self):
        """Test that mole is randomly selected."""
        game = HeistGame(self.config_path)
        game._select_random_mole()

        self.assertIsNotNone(game.mole_agent)
        self.assertIn(game.mole_agent, game.system.agents.keys())

    def test_sabotage_injection(self):
        """Test that sabotage instructions are injected."""
        game = HeistGame(self.config_path)
        game._select_random_mole()

        original_prompt = game.system.agents[game.mole_agent].config.system_prompt
        game._inject_sabotage_behavior()
        modified_prompt = game.system.agents[game.mole_agent].config.system_prompt

        self.assertNotEqual(original_prompt, modified_prompt)
        self.assertIn('SECRET MISSION', modified_prompt)

    def test_quick_game_execution(self):
        """Test that quick game runs without errors."""
        game = HeistGame(self.config_path)

        try:
            result = game.quick_game()
            self.assertIn('outcome', result)
            self.assertIn('mole', result)
            self.assertIn('user_guess', result)
            self.assertIn('correct', result)
        except Exception as e:
            self.fail(f"Quick game failed: {e}")


class TestSaboteurDetector(unittest.TestCase):
    """Test saboteur detection algorithm."""

    @classmethod
    def setUpClass(cls):
        """Setup test environment."""
        cls.config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "day_15",
            "agents_config.yaml"
        )
        cls.db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "heist_session.db"
        )

    def test_detector_initialization(self):
        """Test that detector initializes correctly."""
        from day_17.session_manager import SessionAnalyzer

        analyzer = SessionAnalyzer(self.db_path)
        detector = SaboteurDetector(analyzer)

        self.assertIsNotNone(detector)
        self.assertGreater(len(detector.negative_keywords), 0)
        self.assertGreater(len(detector.delay_keywords), 0)

    def test_suspicion_score_calculation(self):
        """Test suspicion score calculation (requires existing session)."""
        from day_17.session_manager import SessionAnalyzer

        analyzer = SessionAnalyzer(self.db_path)
        detector = SaboteurDetector(analyzer)

        sessions = analyzer.get_all_sessions()

        if len(sessions) > 0:
            session_id = sessions[0].session_id
            scores = detector.calculate_suspicion_scores(session_id)

            # Should have scores for all agents
            self.assertGreater(len(scores), 0)

            # Scores should be between 0 and 1
            for agent, score in scores.items():
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)

    def test_prediction(self):
        """Test saboteur prediction (requires existing session)."""
        from day_17.session_manager import SessionAnalyzer

        analyzer = SessionAnalyzer(self.db_path)
        detector = SaboteurDetector(analyzer)

        sessions = analyzer.get_all_sessions()

        if len(sessions) > 0:
            session_id = sessions[0].session_id
            prediction = detector.predict_saboteur(session_id)

            self.assertIn('most_likely', prediction)
            self.assertIn('confidence', prediction)
            self.assertIn('all_scores', prediction)

            # Confidence should be between 0 and 1
            self.assertGreaterEqual(prediction['confidence'], 0.0)
            self.assertLessEqual(prediction['confidence'], 1.0)


class TestPerformance(unittest.TestCase):
    """Performance benchmarks."""

    @classmethod
    def setUpClass(cls):
        """Setup test environment."""
        cls.config_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "day_15",
            "agents_config.yaml"
        )

    def test_conversation_performance(self):
        """Test conversation performance."""
        system = IntegratedSystem(self.config_path)

        start = time.time()
        system.run_conversation(num_turns=2)
        duration = time.time() - start

        print(f"\n⏱️  Conversation (2 turns) took {duration:.2f}s")

        # Should complete in reasonable time (depends on LLM)
        # This is a loose benchmark
        self.assertLess(duration, 120.0)  # 2 minutes max

    def test_database_query_performance(self):
        """Test database query performance."""
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "heist_session.db"
        )

        manager = SessionManager(db_path)

        start = time.time()
        sessions = manager.list_sessions()
        duration = time.time() - start

        print(f"\n⏱️  Database query took {duration*1000:.2f}ms")

        # Should be very fast
        self.assertLess(duration, 1.0)  # 1 second max


def run_integration_tests():
    """Run all integration tests."""
    print("=" * 80)
    print("Day 23: Integration Tests")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestHeistGame))
    suite.addTests(loader.loadTestsFromTestCase(TestSaboteurDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
