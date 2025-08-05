"""
Integration test for vulnhuntr enhanced features.
Tests the complete flow with rate limiting and state recovery.
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from enhanced_main import EnhancedVulnhuntr
from simple_state import SimpleStateManager
from simple_config import get_config


def create_test_repo():
    """Create a temporary test repository with Python files"""
    
    # Create temporary directory
    test_repo = Path(tempfile.mkdtemp(prefix="vulnhuntr_test_"))
    
    # Create test Python files
    test_files = {
        "app.py": '''
import os
from flask import Flask, request

app = Flask(__name__)

@app.route('/test')
def test_endpoint():
    user_input = request.args.get('input')
    # Potential RCE vulnerability
    return eval(user_input)

if __name__ == '__main__':
    app.run()
''',
        "utils.py": '''
import subprocess

def run_command(cmd):
    # Potential command injection
    return subprocess.run(cmd, shell=True, capture_output=True)

def safe_function():
    return "This is safe"
''',
        "config.py": '''
import json

def load_config(filename):
    with open(filename, 'r') as f:
        return json.load(f)

DATABASE_URL = "sqlite:///app.db"
''',
        "README.md": '''
# Test Application

This is a test Flask application for vulnerability scanning.

## Features
- Web interface
- Command execution
- Configuration management
'''
    }
    
    for filename, content in test_files.items():
        file_path = test_repo / filename
        with open(file_path, 'w') as f:
            f.write(content)
    
    return test_repo


def test_enhanced_features_disabled():
    """Test that enhanced features can be disabled"""
    print("Testing enhanced features disabled...")
    
    vulnhuntr = EnhancedVulnhuntr(enable_enhanced_features=False)
    assert not vulnhuntr.enhanced_features, "Enhanced features should be disabled"
    assert vulnhuntr.state_manager is None, "State manager should be None"
    
    print("  ✓ Enhanced features disabled correctly")


def test_session_management():
    """Test session creation and management"""
    print("Testing session management...")
    
    # Create temporary state file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_state_file = f.name
    
    try:
        state_manager = SimpleStateManager(temp_state_file)
        
        # Create test session
        files = ['test1.py', 'test2.py']
        session_id = state_manager.start_session('/test/repo', files)
        
        # Test session info
        session_info = state_manager.get_session_info(session_id)
        assert session_info['status'] == 'running', "Session should be running"
        assert session_info['total_files'] == 2, "Should have 2 files"
        
        # Test pending files
        pending = state_manager.get_pending_files(session_id)
        assert len(pending) == 2, "Should have 2 pending files"
        
        print(f"  Created session: {session_id}")
        print("  ✓ Session management working correctly")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


def test_rate_limiting_integration():
    """Test rate limiting integration with enhanced LLM"""
    print("Testing rate limiting integration...")
    
    from enhanced_llm import EnhancedLLM
    from simple_rate_limiter import get_rate_limiter
    
    # Create enhanced LLM
    llm = EnhancedLLM(system_prompt="Test", provider_name="claude")
    
    # Check rate limiter is attached
    assert llm.rate_limiter is not None, "Rate limiter should be attached"
    assert llm.provider_name == "claude", "Provider name should be set"
    
    # Test rate limiter status
    status = llm.get_rate_limiter_status()
    assert status is not None, "Should get rate limiter status"
    assert 'tokens' in status, "Status should include tokens"
    
    print(f"  Rate limiter status: {status}")
    print("  ✓ Rate limiting integration working correctly")


def test_config_integration():
    """Test configuration integration"""
    print("Testing configuration integration...")
    
    config = get_config()
    
    # Test that config values are reasonable
    claude_limit = config.get_rate_limit('claude')
    assert claude_limit > 0, "Claude rate limit should be positive"
    assert claude_limit <= 1000, "Claude rate limit should be reasonable"
    
    retry_config = config.get_retry_config()
    assert retry_config['max_retries'] >= 1, "Should have at least 1 retry"
    assert retry_config['base_delay'] > 0, "Base delay should be positive"
    
    print(f"  Claude rate limit: {claude_limit}/min")
    print(f"  Max retries: {retry_config['max_retries']}")
    print("  ✓ Configuration integration working correctly")


def test_cli_help():
    """Test CLI help functionality"""
    print("Testing CLI help...")
    
    from cli import print_help
    
    # This should not raise an exception
    try:
        print_help()
        print("  ✓ CLI help working correctly")
    except Exception as e:
        print(f"  ✗ CLI help failed: {e}")
        raise


def test_mock_analysis_flow():
    """Test the analysis flow with mock data (without actual LLM calls)"""
    print("Testing mock analysis flow...")
    
    test_repo = create_test_repo()
    
    try:
        # Create enhanced vulnhuntr instance
        vulnhuntr = EnhancedVulnhuntr(enable_enhanced_features=True)
        
        # Test that we can create a session
        files = list(test_repo.glob("*.py"))
        assert len(files) >= 2, "Should have at least 2 Python files"
        
        if vulnhuntr.state_manager:
            session_id = vulnhuntr.state_manager.start_session(str(test_repo), [str(f) for f in files])
            assert session_id, "Should create session ID"
            
            # Test session info
            session_info = vulnhuntr.state_manager.get_session_info(session_id)
            assert session_info['repo_path'] == str(test_repo), "Repo path should match"
            assert session_info['total_files'] == len(files), "File count should match"
            
            print(f"  Created session: {session_id}")
            print(f"  Repository: {test_repo}")
            print(f"  Files: {len(files)}")
            print("  ✓ Mock analysis flow working correctly")
        else:
            print("  ✗ State manager not available")
            
    finally:
        # Clean up test repository
        import shutil
        shutil.rmtree(test_repo)


def test_error_handling():
    """Test error handling in enhanced features"""
    print("Testing error handling...")
    
    # Test with invalid state file path
    try:
        state_manager = SimpleStateManager("/invalid/path/state.json")
        # Should create empty state, not crash
        assert state_manager.state is not None, "Should have valid state"
        print("  ✓ Invalid state file handled correctly")
    except Exception as e:
        print(f"  ✗ Error handling failed: {e}")
        raise
    
    # Test with invalid session ID
    state_manager = SimpleStateManager()
    session_info = state_manager.get_session_info("invalid_session")
    assert session_info is None, "Should return None for invalid session"
    
    print("  ✓ Error handling working correctly")


def run_integration_tests():
    """Run all integration tests"""
    print("Running Vulnhuntr Integration Tests")
    print("=" * 50)
    
    tests = [
        test_enhanced_features_disabled,
        test_session_management,
        test_rate_limiting_integration,
        test_config_integration,
        test_cli_help,
        test_mock_analysis_flow,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Integration Tests Complete: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)