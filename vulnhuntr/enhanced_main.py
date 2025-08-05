"""
Enhanced main module for vulnhuntr with rate limiting and state recovery.
Integrates with the existing analysis loop while adding resilience features.
"""

import json
import argparse
import structlog
import time
from pathlib import Path
from typing import List, Optional

from vulnhuntr.__main__ import RepoOps, SymbolExtractor, print_readable, extract_between_tags
from vulnhuntr.enhanced_providers import initialize_llm_enhanced, print_provider_status
from vulnhuntr.simple_state import SimpleStateManager
from vulnhuntr.simple_config import get_config, print_env_help
from vulnhuntr.prompts import *


class EnhancedVulnhuntr:
    """Enhanced vulnerability scanner with state recovery and rate limiting"""
    
    def __init__(self, enable_enhanced_features: bool = True):
        self.config = get_config()
        self.state_manager = SimpleStateManager() if enable_enhanced_features else None
        self.enhanced_features = enable_enhanced_features
        self.session_id = None
        
        # Set up logging
        self.log = structlog.get_logger("vulnhuntr.enhanced")
    
    def run_analysis(self, repo_path: str, analyze_path: str = None, 
                    llm_provider: str = 'claude', resume_session: str = None,
                    verbosity: int = 0) -> bool:
        """
        Run vulnerability analysis with enhanced features.
        
        Args:
            repo_path: Path to repository root
            analyze_path: Specific path to analyze (optional)
            llm_provider: LLM provider to use
            resume_session: Session ID to resume (optional)
            verbosity: Verbosity level
            
        Returns:
            True if analysis completed successfully
        """
        
        if resume_session and self.enhanced_features:
            return self._resume_analysis(resume_session, llm_provider, verbosity)
        else:
            return self._run_new_analysis(repo_path, analyze_path, llm_provider, verbosity)
    
    def _resume_analysis(self, session_id: str, llm_provider: str, verbosity: int) -> bool:
        """Resume an existing analysis session"""
        
        if not self.state_manager:
            print("Error: Enhanced features not enabled, cannot resume session")
            return False
        
        # Get session info
        session_info = self.state_manager.get_session_info(session_id)
        if not session_info:
            print(f"Error: Session {session_id} not found")
            return False
        
        if session_info['status'] == 'completed':
            print(f"Session {session_id} already completed")
            return True
        
        # Get pending files
        pending_files = self.state_manager.get_pending_files(session_id)
        if not pending_files:
            print(f"No pending files in session {session_id}")
            self.state_manager.complete_session(session_id)
            return True
        
        print(f"Resuming session {session_id}")
        print(f"Repository: {session_info['repo_path']}")
        print(f"Progress: {session_info['completed_files']}/{session_info['total_files']} files")
        print(f"Pending files: {len(pending_files)}")
        
        self.session_id = session_id
        
        # Initialize LLM
        llm = initialize_llm_enhanced(llm_provider)
        if verbosity > 0:
            print_provider_status(llm)
        
        # Process pending files
        return self._process_files(pending_files, llm, session_info['repo_path'], verbosity)
    
    def _run_new_analysis(self, repo_path: str, analyze_path: str, 
                         llm_provider: str, verbosity: int) -> bool:
        """Run new analysis session"""
        
        # Set up repository operations
        repo = RepoOps(repo_path)
        code_extractor = SymbolExtractor(repo_path)
        
        # Get files to analyze
        files = list(repo.get_relevant_py_files())
        
        if analyze_path:
            # User specified --analyze flag
            analyze_path_obj = Path(analyze_path)
            if analyze_path_obj.is_absolute():
                files_to_analyze = list(repo.get_files_to_analyze(analyze_path_obj))
            else:
                files_to_analyze = list(repo.get_files_to_analyze(Path(repo_path) / analyze_path_obj))
        else:
            # Analyze the entire project for network-related files
            files_to_analyze = list(repo.get_network_related_files(files))
        
        if not files_to_analyze:
            print("No files to analyze found")
            return False
        
        print(f"Found {len(files_to_analyze)} files to analyze")
        
        # Create session if enhanced features enabled
        if self.enhanced_features and self.state_manager:
            file_paths = [str(f) for f in files_to_analyze]
            self.session_id = self.state_manager.start_session(repo_path, file_paths)
            print(f"Created session: {self.session_id}")
        
        # Initialize LLM
        llm = initialize_llm_enhanced(llm_provider)
        if verbosity > 0:
            print_provider_status(llm)
        
        # Get README summary (from original implementation)
        readme_content = repo.get_readme_content()
        summary = ""
        if readme_content:
            self.log.info("Summarizing project README")
            try:
                summary_response = llm.chat(
                    (ReadmeContent(content=readme_content).to_xml() + b'\n' +
                     Instructions(instructions=README_SUMMARY_PROMPT_TEMPLATE).to_xml()
                    ).decode()
                )
                summary = extract_between_tags("summary", summary_response)[0]
                self.log.info("README summary complete", summary=summary)
            except Exception as e:
                self.log.warning("Failed to generate README summary", error=str(e))
        
        # Initialize system prompt
        system_prompt = (Instructions(instructions=SYS_PROMPT_TEMPLATE).to_xml() + b'\n' +
                        ReadmeSummary(readme_summary=summary).to_xml()
                        ).decode()
        
        # Reinitialize LLM with system prompt
        llm = initialize_llm_enhanced(llm_provider, system_prompt)
        
        # Process files
        return self._process_files(files_to_analyze, llm, repo_path, verbosity, code_extractor)
    
    def _process_files(self, files_to_analyze: List, llm, repo_path: str, 
                      verbosity: int, code_extractor: SymbolExtractor = None) -> bool:
        """Process list of files for analysis"""
        
        if code_extractor is None:
            code_extractor = SymbolExtractor(repo_path)
        
        processed_count = 0
        failed_count = 0
        
        try:
            for py_f in files_to_analyze:
                file_path = str(py_f)
                
                try:
                    # Check cache first if enhanced features enabled
                    if self.enhanced_features and self.state_manager:
                        cached_result = self.state_manager.get_cached_result(file_path)
                        if cached_result:
                            print(f"\n[CACHED] {file_path}")
                            if verbosity > 0:
                                print_readable(cached_result)
                            processed_count += 1
                            continue
                        
                        # Check if file previously failed
                        if self.state_manager.is_file_failed(file_path):
                            print(f"\n[SKIPPED] {file_path} (previously failed)")
                            processed_count += 1
                            continue
                    
                    print(f"\n[ANALYZING] {file_path}")
                    
                    # Process file (adapted from original __main__.py)
                    result = self._analyze_file(py_f, llm, code_extractor, verbosity)
                    
                    if result:
                        # Save result if enhanced features enabled
                        if self.enhanced_features and self.state_manager and self.session_id:
                            if hasattr(result, 'model_dump'):
                                result_dict = result.model_dump()
                            else:
                                result_dict = result
                            self.state_manager.mark_file_completed(self.session_id, file_path, result_dict)
                        
                        processed_count += 1
                        
                        if verbosity == 0:  # Only print if not verbose (verbose prints during analysis)
                            print_readable(result)
                    
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    failed_count += 1
                    
                    # Mark as failed if enhanced features enabled
                    if self.enhanced_features and self.state_manager and self.session_id:
                        self.state_manager.mark_file_failed(self.session_id, file_path, str(e))
                    
                    if verbosity > 0:
                        import traceback
                        traceback.print_exc()
                    
                    continue
                
                # Progress update
                total_files = len(files_to_analyze)
                current_progress = processed_count + failed_count
                print(f"Progress: {current_progress}/{total_files} files processed")
                
                # Update session progress
                if self.enhanced_features and self.state_manager and self.session_id:
                    self.state_manager.get_session_info(self.session_id)  # This updates last_updated
            
            # Complete session
            if self.enhanced_features and self.state_manager and self.session_id:
                self.state_manager.complete_session(self.session_id)
                print(f"\nSession {self.session_id} completed!")
            
            print(f"\nAnalysis completed: {processed_count} successful, {failed_count} failed")
            return failed_count == 0
            
        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user")
            if self.enhanced_features and self.state_manager and self.session_id:
                print(f"Session {self.session_id} can be resumed later")
            return False
        
        except Exception as e:
            print(f"Analysis failed: {e}")
            if self.enhanced_features and self.state_manager and self.session_id:
                self.state_manager.fail_session(self.session_id, str(e))
            return False
    
    def _analyze_file(self, py_f: Path, llm, code_extractor: SymbolExtractor, verbosity: int):
        """Analyze individual file (adapted from original implementation)"""
        
        with py_f.open(encoding='utf-8') as f:
            content = f.read()
            if not len(content):
                return None
        
        print(f"Analyzing {py_f}")
        print('-' * 40 + '\n')
        
        # Initial analysis (from original __main__.py)
        user_prompt = (
            FileCode(file_path=str(py_f), file_source=content).to_xml() + b'\n' +
            Instructions(instructions=INITIAL_ANALYSIS_PROMPT_TEMPLATE).to_xml() + b'\n' +
            AnalysisApproach(analysis_approach=ANALYSIS_APPROACH_TEMPLATE).to_xml() + b'\n' +
            PreviousAnalysis(previous_analysis='').to_xml() + b'\n' +
            Guidelines(guidelines=GUIDELINES_TEMPLATE).to_xml() + b'\n' +
            ResponseFormat(response_format=json.dumps(Response.model_json_schema(), indent=4)).to_xml()
        ).decode()
        
        initial_analysis_report = llm.chat(user_prompt, response_model=Response)
        self.log.info("Initial analysis complete", report=initial_analysis_report.model_dump())
        
        if verbosity > 0:
            print_readable(initial_analysis_report)
        
        # Secondary analysis (simplified version of original)
        if initial_analysis_report.confidence_score > 0 and len(initial_analysis_report.vulnerability_types):
            
            for vuln_type in initial_analysis_report.vulnerability_types:
                if verbosity > 0:
                    print(f"\nPerforming secondary analysis for {vuln_type}")
                
                # Simplified secondary analysis (could be enhanced further)
                vuln_specific_prompt = (
                    FileCode(file_path=str(py_f), file_source=content).to_xml() + b'\n' +
                    ExampleBypasses(
                        example_bypasses='\n'.join(VULN_SPECIFIC_BYPASSES_AND_PROMPTS[vuln_type]['bypasses'])
                    ).to_xml() + b'\n' +
                    Instructions(instructions=VULN_SPECIFIC_BYPASSES_AND_PROMPTS[vuln_type]['prompt']).to_xml() + b'\n' +
                    ResponseFormat(response_format=json.dumps(Response.model_json_schema(), indent=4)).to_xml()
                ).decode()
                
                try:
                    secondary_analysis_report = llm.chat(vuln_specific_prompt, response_model=Response)
                    
                    if verbosity > 0:
                        print_readable(secondary_analysis_report)
                    
                    # Use secondary analysis if it has higher confidence
                    if secondary_analysis_report.confidence_score > initial_analysis_report.confidence_score:
                        initial_analysis_report = secondary_analysis_report
                        
                except Exception as e:
                    if verbosity > 0:
                        print(f"Secondary analysis failed: {e}")
                    continue
        
        return initial_analysis_report
    
    def list_sessions(self):
        """List available sessions"""
        if not self.enhanced_features or not self.state_manager:
            print("Enhanced features not enabled")
            return
        
        sessions = self.state_manager.list_sessions()
        if not sessions:
            print("No sessions found")
            return
        
        print("Available sessions:")
        print("-" * 80)
        print(f"{'ID':<10} {'Repository':<30} {'Status':<12} {'Progress':<12} {'Last Updated'}")
        print("-" * 80)
        
        for session in sessions:
            last_updated = time.strftime('%Y-%m-%d %H:%M', time.localtime(session['last_updated']))
            print(f"{session['id']:<10} {session['repo_path'][-30:]:<30} {session['status']:<12} {session['progress']:<12} {last_updated}")
    
    def get_statistics(self):
        """Get and print analysis statistics"""
        if not self.enhanced_features or not self.state_manager:
            print("Enhanced features not enabled")
            return
        
        stats = self.state_manager.get_statistics()
        print("Analysis Statistics:")
        print(f"  Total sessions: {stats['total_sessions']}")
        print(f"  Completed sessions: {stats['completed_sessions']}")
        print(f"  Running sessions: {stats['running_sessions']}")
        print(f"  Failed sessions: {stats['failed_sessions']}")
        print(f"  Total files processed: {stats['total_files_processed']}")
        print(f"  Successful files: {stats['successful_files']}")
        print(f"  Failed files: {stats['failed_files']}")
        print(f"  Cache hit rate: {stats['cache_hit_rate']}")


def create_enhanced_parser():
    """Create argument parser with enhanced options"""
    
    parser = argparse.ArgumentParser(
        description='Enhanced Vulnhuntr with rate limiting and state recovery'
    )
    
    # Original arguments (maintained for compatibility)
    parser.add_argument('-r', '--root', type=str, required=True,
                       help='Path to the root directory of the project')
    parser.add_argument('-a', '--analyze', type=str,
                       help='Specific path or file within the project to analyze')
    parser.add_argument('-l', '--llm', type=str, 
                       choices=['claude', 'gpt', 'openrouter', 'ollama'], 
                       default='claude',
                       help='LLM client to use (default: claude)')
    parser.add_argument('-v', '--verbosity', action='count', default=0,
                       help='Increase output verbosity (-v for INFO, -vv for DEBUG)')
    
    # Enhanced arguments
    parser.add_argument('--resume', type=str,
                       help='Resume analysis from session ID')
    parser.add_argument('--list-sessions', action='store_true',
                       help='List resumable analysis sessions')
    parser.add_argument('--stats', action='store_true',
                       help='Show analysis statistics')
    parser.add_argument('--no-enhanced', action='store_true',
                       help='Disable enhanced features (rate limiting, state recovery)')
    parser.add_argument('--config-help', action='store_true',
                       help='Show configuration help')
    
    return parser


def run_enhanced():
    """Enhanced main function"""
    
    parser = create_enhanced_parser()
    args = parser.parse_args()
    
    # Handle utility commands
    if args.config_help:
        print_env_help()
        return
    
    # Create enhanced vulnhuntr instance
    enhanced_features = not args.no_enhanced
    vulnhuntr = EnhancedVulnhuntr(enable_enhanced_features=enhanced_features)
    
    if args.list_sessions:
        vulnhuntr.list_sessions()
        return
    
    if args.stats:
        vulnhuntr.get_statistics()
        return
    
    # Run analysis
    success = vulnhuntr.run_analysis(
        repo_path=args.root,
        analyze_path=args.analyze,
        llm_provider=args.llm,
        resume_session=args.resume,
        verbosity=args.verbosity
    )
    
    exit(0 if success else 1)


if __name__ == '__main__':
    run_enhanced()