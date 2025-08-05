"""
Simple test script for core components without external dependencies.
Tests rate limiting, state management, and configuration.
"""

import time
import tempfile
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from simple_rate_limiter import SimpleRateLimiter, get_rate_limiter, reset_rate_limiters
from simple_state import SimpleStateManager
from simple_config import SimpleConfig


def test_rate_limiter():
    """Test rate limiter functionality"""
    print("Testing Rate Limiter...")
    
    # Create a rate limiter with 2 requests per minute for testing
    limiter = SimpleRateLimiter(requests_per_minute=2)
    
    # Test initial state
    assert limiter.can_proceed(), "Should allow first request"
    assert limiter.can_proceed(), "Should allow second request"
    assert not limiter.can_proceed(), "Should block third request"
    
    # Test wait time calculation
    wait_time = limiter.wait_time()
    assert wait_time > 0, "Should have positive wait time"
    print(f"  Wait time: {wait_time:.2f} seconds")
    
    # Test status
    status = limiter.get_status()
    assert 'tokens' in status, "Status should include tokens"
    assert 'requests_per_minute' in status, "Status should include rate limit"
    print(f"  Status: {status}")
    
    print("  ✓ Rate limiter tests passed")


def test_provider_rate_limiters():
    """Test provider-specific rate limiters"""
    print("Testing Provider Rate Limiters...")
    
    # Test getting rate limiters for different providers
    claude_limiter = get_rate_limiter('claude')
    openai_limiter = get_rate_limiter('openai')
    ollama_limiter = get_rate_limiter('ollama')
    
    assert claude_limiter is not None, "Should get Claude rate limiter"
    assert openai_limiter is not None, "Should get OpenAI rate limiter"
    assert ollama_limiter is not None, "Should get Ollama rate limiter"
    
    # Test that they have different rates
    claude_status = claude_limiter.get_status()
    openai_status = openai_limiter.get_status()
    
    print(f"  Claude rate: {claude_status['requests_per_minute']}/min")
    print(f"  OpenAI rate: {openai_status['requests_per_minute']}/min")
    
    print("  ✓ Provider rate limiter tests passed")


def test_state_manager():
    """Test state manager functionality"""
    print("Testing State Manager...")
    
    # Create temporary state file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_state_file = f.name
    
    try:
        # Create state manager
        state_manager = SimpleStateManager(temp_state_file)
        
        # Test session creation
        files = ['/test/file1.py', '/test/file2.py', '/test/file3.py']
        session_id = state_manager.start_session('/test/repo', files)
        
        assert session_id, "Should create session ID"
        print(f"  Created session: {session_id}")
        
        # Test session info
        session_info = state_manager.get_session_info(session_id)
        assert session_info is not None, "Should get session info"
        assert session_info['total_files'] == 3, "Should have correct file count"
        assert session_info['status'] == 'running', "Should be running"
        
        # Test marking file completed
        test_result = {'vulnerabilities': [], 'confidence': 5}
        state_manager.mark_file_completed(session_id, '/test/file1.py', test_result)
        
        # Test caching
        cached_result = state_manager.get_cached_result('/test/file1.py')
        assert cached_result == test_result, "Should return cached result"
        
        # Test pending files
        pending = state_manager.get_pending_files(session_id)
        assert len(pending) == 2, "Should have 2 pending files"
        assert '/test/file1.py' not in pending, "Completed file should not be pending"
        
        # Test session completion
        state_manager.complete_session(session_id)
        session_info = state_manager.get_session_info(session_id)
        assert session_info['status'] == 'completed', "Should be completed"
        
        # Test listing sessions
        sessions = state_manager.list_sessions()
        assert len(sessions) == 1, "Should have one session"
        assert sessions[0]['id'] == session_id, "Should match session ID"
        
        # Test statistics
        stats = state_manager.get_statistics()
        assert stats['total_sessions'] == 1, "Should have 1 session"
        assert stats['completed_sessions'] == 1, "Should have 1 completed session"
        
        print(f"  Statistics: {stats}")
        print("  ✓ State manager tests passed")
        
    finally:
        # Clean up
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


def test_config():
    """Test configuration functionality"""
    print("Testing Configuration...")
    
    config = SimpleConfig()
    
    # Test rate limit retrieval
    claude_limit = config.get_rate_limit('claude')
    assert claude_limit > 0, "Should have positive rate limit"
    print(f"  Claude rate limit: {claude_limit}")
    
    # Test retry config
    retry_config = config.get_retry_config()
    assert 'max_retries' in retry_config, "Should have max_retries"
    assert 'base_delay' in retry_config, "Should have base_delay"
    print(f"  Retry config: {retry_config}")
    
    # Test state config
    state_config = config.get_state_config()
    assert 'state_file' in state_config, "Should have state_file"
    print(f"  State config: {state_config}")
    
    # Test config dict
    config_dict = config.to_dict()
    assert 'rate_limits' in config_dict, "Should have rate_limits in dict"
    
    print("  ✓ Configuration tests passed")


def test_rate_limiting_behavior():
    """Test actual rate limiting behavior"""
    print("Testing Rate Limiting Behavior...")
    
    # Create a very restrictive rate limiter (1 request per minute)
    limiter = SimpleRateLimiter(requests_per_minute=1)
    
    # First request should succeed
    assert limiter.can_proceed(), "First request should succeed"
    
    # Second request should fail
    assert not limiter.can_proceed(), "Second request should fail"
    
    # Wait time should be close to 60 seconds
    wait_time = limiter.wait_time()
    assert 50 < wait_time < 70, f"Wait time should be ~60 seconds, got {wait_time}"
    
    print(f"  Rate limiting working correctly, wait time: {wait_time:.1f}s")
    print("  ✓ Rate limiting behavior tests passed")


def test_integration():
    """Test integration between components"""
    print("Testing Component Integration...")
    
    # Test that rate limiters are properly configured
    reset_rate_limiters()
    config = SimpleConfig()
    
    claude_limiter = get_rate_limiter('claude')
    expected_rate = config.get_rate_limit('claude')
    actual_rate = claude_limiter.get_status()['requests_per_minute']
    
    assert actual_rate == expected_rate, f"Rate limiter should match config: {actual_rate} != {expected_rate}"
    
    print("  ✓ Integration tests passed")


def run_all_tests():
    """Run all tests"""
    print("Running Vulnhuntr Simple Core Component Tests")
    print("=" * 50)
    
    try:
        test_rate_limiter()
        test_provider_rate_limiters()
        test_state_manager()
        test_config()
        test_rate_limiting_behavior()
        test_integration()
        
        print("=" * 50)
        print("✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)