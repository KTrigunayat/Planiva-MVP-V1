"""
Test runner for API and system tests in Event Planning Agent v2

Executes comprehensive API endpoint tests, system health monitoring tests,
and load testing for concurrent workflow execution.

Requirements: 5.1, 6.4, 6.5
"""

import sys
import os
import subprocess
import time
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from observability.logging import get_logger

logger = get_logger(__name__, component="test_runner")


class TestRunner:
    """Comprehensive test runner for API and system tests"""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.start_time = datetime.utcnow()
        self.test_directory = Path(__file__).parent
        
    def run_test_suite(self, test_file: str, test_name: str, verbose: bool = True) -> Dict[str, Any]:
        """Run a specific test suite"""
        logger.info(f"Running {test_name} tests from {test_file}")
        
        start_time = time.time()
        
        # Construct pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_directory / test_file),
            "-v" if verbose else "-q",
            "--tb=short",
            "--json-report",
            f"--json-report-file={self.test_directory / f'{test_name}_results.json'}"
        ]
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            # Parse results
            test_result = {
                "test_name": test_name,
                "test_file": test_file,
                "duration_seconds": duration,
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Try to load JSON report if available
            json_report_file = self.test_directory / f'{test_name}_results.json'
            if json_report_file.exists():
                try:
                    with open(json_report_file, 'r') as f:
                        json_report = json.load(f)
                        test_result["detailed_results"] = json_report
                except Exception as e:
                    logger.warning(f"Could not parse JSON report: {e}")
            
            self.test_results[test_name] = test_result
            
            if test_result["success"]:
                logger.info(f"✅ {test_name} tests passed ({duration:.2f}s)")
            else:
                logger.error(f"❌ {test_name} tests failed ({duration:.2f}s)")
                logger.error(f"Error output: {result.stderr}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            test_result = {
                "test_name": test_name,
                "test_file": test_file,
                "duration_seconds": duration,
                "return_code": -1,
                "success": False,
                "error": "Test suite timed out after 5 minutes"
            }
            
            self.test_results[test_name] = test_result
            logger.error(f"⏰ {test_name} tests timed out ({duration:.2f}s)")
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": test_name,
                "test_file": test_file,
                "duration_seconds": duration,
                "return_code": -1,
                "success": False,
                "error": str(e)
            }
            
            self.test_results[test_name] = test_result
            logger.error(f"💥 {test_name} tests failed with exception: {e}")
            return test_result
    
    def run_all_api_system_tests(self) -> Dict[str, Any]:
        """Run all API and system tests"""
        logger.info("🚀 Starting comprehensive API and system test suite")
        
        # Test suites to run
        test_suites = [
            ("test_api_endpoints.py", "api_endpoints"),
            ("test_system_health.py", "system_health"),
            ("test_load_testing.py", "load_testing")
        ]
        
        # Run each test suite
        for test_file, test_name in test_suites:
            self.run_test_suite(test_file, test_name)
        
        # Generate summary
        summary = self.generate_test_summary()
        
        # Save comprehensive report
        self.save_test_report(summary)
        
        return summary
    
    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        summary = {
            "test_run_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "total_duration_seconds": total_duration,
                "test_suites_run": len(self.test_results)
            },
            "overall_results": {
                "all_tests_passed": all(result["success"] for result in self.test_results.values()),
                "successful_suites": sum(1 for result in self.test_results.values() if result["success"]),
                "failed_suites": sum(1 for result in self.test_results.values() if not result["success"]),
                "total_suites": len(self.test_results)
            },
            "test_suite_results": self.test_results,
            "recommendations": self.generate_recommendations()
        }
        
        return summary
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for failed tests
        failed_suites = [name for name, result in self.test_results.items() if not result["success"]]
        
        if failed_suites:
            recommendations.append(f"❌ Failed test suites: {', '.join(failed_suites)}")
            recommendations.append("🔧 Review error logs and fix failing tests before deployment")
        
        # Check for performance issues
        slow_suites = [
            name for name, result in self.test_results.items() 
            if result.get("duration_seconds", 0) > 60
        ]
        
        if slow_suites:
            recommendations.append(f"⚠️ Slow test suites (>60s): {', '.join(slow_suites)}")
            recommendations.append("🚀 Consider optimizing test performance or splitting large test suites")
        
        # Check load testing results
        if "load_testing" in self.test_results:
            load_result = self.test_results["load_testing"]
            if not load_result["success"]:
                recommendations.append("🔥 Load testing failed - system may not handle concurrent load well")
                recommendations.append("📊 Review system resource allocation and scaling configuration")
        
        # Check system health tests
        if "system_health" in self.test_results:
            health_result = self.test_results["system_health"]
            if not health_result["success"]:
                recommendations.append("🏥 System health monitoring tests failed")
                recommendations.append("🔍 Review health check configuration and monitoring setup")
        
        # Check API tests
        if "api_endpoints" in self.test_results:
            api_result = self.test_results["api_endpoints"]
            if not api_result["success"]:
                recommendations.append("🌐 API endpoint tests failed")
                recommendations.append("🔗 Review API compatibility and error handling")
        
        if not recommendations:
            recommendations.append("✅ All tests passed successfully!")
            recommendations.append("🚀 System is ready for deployment")
        
        return recommendations
    
    def save_test_report(self, summary: Dict[str, Any]):
        """Save comprehensive test report"""
        report_file = self.test_directory / f"api_system_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"📄 Test report saved to: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save test report: {e}")
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "="*80)
        print("🧪 API AND SYSTEM TEST SUMMARY")
        print("="*80)
        
        # Overall results
        overall = summary["overall_results"]
        print(f"\n📊 Overall Results:")
        print(f"   Total Test Suites: {overall['total_suites']}")
        print(f"   Successful: {overall['successful_suites']}")
        print(f"   Failed: {overall['failed_suites']}")
        print(f"   Success Rate: {(overall['successful_suites']/overall['total_suites']*100):.1f}%")
        
        # Duration
        duration = summary["test_run_info"]["total_duration_seconds"]
        print(f"   Total Duration: {duration:.2f} seconds")
        
        # Individual test results
        print(f"\n📋 Test Suite Results:")
        for name, result in summary["test_suite_results"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result.get("duration_seconds", 0)
            print(f"   {status} {name:<20} ({duration:.2f}s)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        for rec in summary["recommendations"]:
            print(f"   {rec}")
        
        print("\n" + "="*80)


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run API and system tests for Event Planning Agent v2")
    parser.add_argument("--suite", choices=["api", "health", "load", "all"], default="all",
                       help="Test suite to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.suite == "all":
        summary = runner.run_all_api_system_tests()
    elif args.suite == "api":
        runner.run_test_suite("test_api_endpoints.py", "api_endpoints", verbose=args.verbose)
        summary = runner.generate_test_summary()
    elif args.suite == "health":
        runner.run_test_suite("test_system_health.py", "system_health", verbose=args.verbose)
        summary = runner.generate_test_summary()
    elif args.suite == "load":
        runner.run_test_suite("test_load_testing.py", "load_testing", verbose=args.verbose)
        summary = runner.generate_test_summary()
    
    if not args.quiet:
        runner.print_summary(summary)
    
    # Exit with appropriate code
    if summary["overall_results"]["all_tests_passed"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()