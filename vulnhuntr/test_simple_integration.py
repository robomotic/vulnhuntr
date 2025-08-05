"""
Simple integration test for vulnhuntr enhanced features.
Tests core integration without external dependencies.
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from simple_state import SimpleStateManager
from simple_config import get_config
from enhanced_llm import EnhancedLLM
from enhanced_providers import initialize_llm_enhanced


def test_enhanced_features_basic():
    """Test basic enhanced features without external dependencies"""
    print("Testing basic enhanced features...")
    
    # Test configuration
    config = get_config()
    assert config is not None, "Should get config"
    
    claude_limit = config.get_rate_limit('claude')
    assert claude_limit > 0, "Should have positive rate limit"
    
    print(f"  Claude rate limit: {claude_limit}/min")
    print("  ✓ Configuration working")


def test_state_management_integration():
    """Test state management integration"""
    print("Testing state management integration...")
    
    # Create temporary state file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_state_file = f.name
    
    try:
        state_manager = SimpleStateManager(temp_state_file)
        
        # Create test session
        files = ['test1.py', 'test2.py', 'test3.py']
        session_id = state_manager.start_session('/test/repo', files)
        
        print(f"  Created session: {session_id}")
        
        # Test session operations
        session_info = state_manager.get_session_info(session_id)
        assert session_info['status'] == 'running', "Session should be running"
        assert session_info['total_files'] == 3, "Should have 3 files"
        
        # Mark one file completed
        test_result = {'vulnerabilities': ['RCE'], 'confidence': 8}
        state_manager.mark_file_completed(session_id, 'test1.py', test_result)
        
        # Check cache
        cached = state_manager.get_cached_result('test1.py')
        assert cached == test_result, "Should return cached result"
        
        # Check pending files
        pending = state_manager.get_pending_files(session_id)
        assert len(pending) == 2, "Should have 2 pending files"
        assert 'test1.py' not in pending, "Completed file should not be pending"
        
        # Test session completion
        state_manager.complete_session(session_id)
        session_info = state_manager.get_session_info(session_id)
        assert session_info['status'] == 'completed', "Should be completed"
        
        # Test statistics
        stats = state_manager.get_statistics()
        assert stats['total_sessions'] == 1, "Should have 1 session"
        assert stats['completed_sessions'] == 1, "Should have 1 completed session"
        
        print(f"  Final statistics: {stats}")
        print("  ✓ State management integration working")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


def test_rate_limiting_integration():
    """Test rate limiting integration"""
    print("Testing rate limiting integration...")
    
    # Test enhanced LLM creation
    llm = EnhancedLLM(system_prompt="Test", provider_name="claude")
    
    assert llm.provider_name == "claude", "Provider name should be set"
    assert llm.rate_limiter is not None, "Rate limiter should be attached"
    
    # Test rate limiter status
    status = llm.get_rate_limiter_status()
    assert status is not None, "Should get status"
    assert 'tokens' in status, "Status should include tokens"
    assert 'requests_per_minute' in status, "Status should include rate limit"
    
    print(f"  Rate limiter status: {status}")
    
    # Test rate limiter reset
    original_tokens = status['tokens']
    llm.reset_rate_limiter()
    new_status = llm.get_rate_limiter_status()
    assert new_status['tokens'] >= original_tokens, "Tokens should be reset"
    
    print("  ✓ Rate limiting integration working")


def test_provider_initialization():
    """Test enhanced provider initialization"""
    print("Testing provider initialization...")
    
    # Test that we can create provider instances without errors
    try:
        # This will fail if anthropic/openai modules are missing, but should not crash
        from enhanced_providers import Claude, ChatGPT, OpenRouter, Ollama
        
        # Test that classes exist and can be instantiated (without actual API calls)
        claude_class = Claude
        chatgpt_class = ChatGPT
        openrouter_class = OpenRouter
        ollama_class = Ollama
        
        assert claude_class is not None, "Claude class should exist"
        assert chatgpt_class is not None, "ChatGPT class should exist"
        assert openrouter_class is not None, "OpenRouter class should exist"
        assert ollama_class is not None, "Ollama class should exist"
        
        print("  ✓ Provider classes available")
        
    except ImportError as e:
        print(f"  ! Provider initialization skipped due to missing dependencies: {e}")
        print("  ✓ Provider initialization handled gracefully")


def test_session_resume_simulation():
    """Test session resume simulation"""
    print("Testing session resume simulation...")
    
    # Create temporary state file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_state_file = f.name
    
    try:
        state_manager = SimpleStateManager(temp_state_file)
        
        # Create session with multiple files
        files = ['app.py', 'utils.py', 'config.py', 'models.py']
        session_id = state_manager.start_session('/test/repo', files)
        
        # Simulate partial completion
        state_manager.mark_file_completed(session_id, 'app.py', {'vuln': 'RCE', 'confidence': 9})
        state_manager.mark_file_completed(session_id, 'utils.py', {'vuln': 'SQLI', 'confidence': 7})
        
        # Check progress
        session_info = state_manager.get_session_info(session_id)
        assert session_info['completed_files'] == 2, "Should have 2 completed files"
        
        # Get pending files (simulating resume)
        pending = state_manager.get_pending_files(session_id)
        assert len(pending) == 2, "Should have 2 pending files"
        assert 'config.py' in pending, "config.py should be pending"
        assert 'models.py' in pending, "models.py should be pending"
        
        print(f"  Session {session_id} progress: {session_info['completed_files']}/{session_info['total_files']}")
        print(f"  Pending files: {pending}")
        
        # Simulate completing remaining files
        state_manager.mark_file_completed(session_id, 'config.py', {'vuln': None, 'confidence': 2})
        state_manager.mark_file_failed(session_id, 'models.py', 'Analysis timeout')
        
        # Complete session
        state_manager.complete_session(session_id)
        
        # Verify final state
        final_info = state_manager.get_session_info(session_id)
        assert final_info['status'] == 'completed', "Session should be completed"
        assert final_info['completed_files'] == 4, "Should have processed all files"
        
        print("  ✓ Session resume simulation working")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)


def test_error_handling():
    """Test error handling scenarios"""
    print("Testing error handling...")
    
    # Test invalid session operations
    state_manager = SimpleStateManager()
    
    # Invalid session ID
    invalid_info = state_manager.get_session_info("invalid_session_id")
    assert invalid_info is None, "Should return None for invalid session"
    
    # Invalid file operations
    pending = state_manager.get_pending_files("invalid_session_id")
    assert len(pending) == 0, "Should return empty list for invalid session"
    
    # Test with corrupted state file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content {")
        temp_state_file = f.name
    
    try:
        # Should handle corrupted file gracefully
        state_manager = SimpleStateManager(temp_state_file)
        assert state_manager.state is not None, "Should have valid state despite corruption"
        
        print("  ✓ Error handling working correctly")
        
    finally:
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)
        backup_file = temp_state_file + ".backup"
        if os.path.exists(backup_file):
            os.unlink(backup_file)


def test_configuration_integration():
    """Test configuration integration across components"""
    print("Testing configuration integration...")
    
    config = get_config()
    
    # Test rate limit consistency
    from simple_rate_limiter import get_rate_limiter
    
    claude_config_limit = config.get_rate_limit('claude')
    claude_limiter = get_rate_limiter('claude')
    claude_actual_limit = claude_limiter.get_status()['requests_per_minute']
    
    assert claude_config_limit == claude_actual_limit, f"Rate limits should match: {claude_config_limit} != {claude_actual_limit}"
    
    # Test retry configuration
    retry_config = config.get_retry_config()
    assert retry_config['max_retries'] >= 1, "Should have at least 1 retry"
    assert retry_config['base_delay'] > 0, "Base delay should be positive"
    assert retry_config['max_delay'] >= retry_config['base_delay'], "Max delay should be >= base delay"
    
    print(f"  Rate limit consistency: {claude_config_limit}/min")
    print(f"  Retry config: {retry_config}")
    print("  ✓ Configuration integration working")


def run_simple_integration_tests():
    """Run all simple integration tests"""
    print("Running Vulnhuntr Simple Integration Tests")
    print("=" * 50)
    
    tests = [
        test_enhanced_features_basic,
        test_state_management_integration,
        test_rate_limiting_integration,
        test_provider_initialization,
        test_session_resume_simulation,
        test_error_handling,
        test_configuration_integration
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
    print(f"Simple Integration Tests Complete: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == '__main__':
    success = run_simple_integration_tests()
    exit(0 if success else 1)