#!/usr/bin/env python3
"""
Performance monitoring script for Event Planning Agent v2.
Monitors system performance, database health, and workflow efficiency.
"""

import asyncio
import json
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import get_connection_manager, test_database_connection
from database.optimized_queries import get_query_manager
from llm.optimized_manager import get_llm_manager
from config.settings import get_settings

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring for Event Planning Agent v2.
    Tracks database, LLM, workflow, and system performance metrics.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.start_time = time.time()
        self.metrics_history = []
        self.alert_thresholds = self._load_alert_thresholds()
        
    def _load_alert_thresholds(self) -> Dict[str, float]:
        """Load performance alert thresholds from environment"""
        return {
            'response_time_warning': float(self.settings.get('RESPONSE_TIME_WARNING', 2000)),
            'response_time_critical': float(self.settings.get('RESPONSE_TIME_CRITICAL', 5000)),
            'error_rate_warning': float(self.settings.get('ERROR_RATE_WARNING', 5)),
            'error_rate_critical': float(self.settings.get('ERROR_RATE_CRITICAL', 10)),
            'cpu_usage_warning': float(self.settings.get('CPU_USAGE_WARNING', 70)),
            'cpu_usage_critical': float(self.settings.get('CPU_USAGE_CRITICAL', 85)),
            'memory_usage_warning': float(self.settings.get('MEMORY_USAGE_WARNING', 75)),
            'memory_usage_critical': float(self.settings.get('MEMORY_USAGE_CRITICAL', 90)),
            'workflow_time_warning': float(self.settings.get('WORKFLOW_TIME_WARNING', 120000)),
            'workflow_time_critical': float(self.settings.get('WORKFLOW_TIME_CRITICAL', 300000))
        }
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg': list(load_avg)
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'percent': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'process': {
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'cpu_percent': process_cpu,
                    'num_threads': process.num_threads(),
                    'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e)}
    
    def collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics"""
        try:
            # Test database connection
            db_status = test_database_connection()
            
            # Get connection manager stats
            conn_manager = get_connection_manager()
            conn_stats = conn_manager.get_connection_stats()
            
            # Get query manager performance
            query_manager = get_query_manager()
            query_stats = query_manager.get_performance_metrics()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'connection_status': db_status,
                'connection_pool': conn_stats,
                'query_performance': query_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return {'error': str(e)}
    
    async def collect_llm_metrics(self) -> Dict[str, Any]:
        """Collect LLM performance metrics"""
        try:
            llm_manager = await get_llm_manager()
            llm_stats = llm_manager.get_performance_metrics()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'llm_performance': llm_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to collect LLM metrics: {e}")
            return {'error': str(e)}
    
    def collect_workflow_metrics(self) -> Dict[str, Any]:
        """Collect workflow performance metrics from database"""
        try:
            from database.connection import get_sync_session
            from database.models import WorkflowMetrics, AgentPerformance
            from sqlalchemy import func, desc
            
            with get_sync_session() as session:
                # Recent workflow metrics (last 24 hours)
                recent_workflows = session.query(WorkflowMetrics).filter(
                    WorkflowMetrics.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).all()
                
                # Aggregate workflow statistics
                workflow_stats = session.query(
                    func.count(WorkflowMetrics.id).label('total_workflows'),
                    func.avg(WorkflowMetrics.total_execution_time_ms).label('avg_execution_time'),
                    func.max(WorkflowMetrics.total_execution_time_ms).label('max_execution_time'),
                    func.min(WorkflowMetrics.total_execution_time_ms).label('min_execution_time'),
                    func.avg(WorkflowMetrics.final_score).label('avg_final_score'),
                    func.avg(WorkflowMetrics.total_iterations).label('avg_iterations')
                ).filter(
                    WorkflowMetrics.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).first()
                
                # Agent performance statistics
                agent_stats = session.query(
                    AgentPerformance.agent_name,
                    func.count(AgentPerformance.id).label('total_executions'),
                    func.avg(AgentPerformance.execution_time_ms).label('avg_execution_time'),
                    func.sum(AgentPerformance.success.cast('integer')).label('successful_executions')
                ).filter(
                    AgentPerformance.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).group_by(AgentPerformance.agent_name).all()
                
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'recent_workflows_count': len(recent_workflows),
                    'workflow_statistics': {
                        'total_workflows': workflow_stats.total_workflows or 0,
                        'avg_execution_time_ms': float(workflow_stats.avg_execution_time or 0),
                        'max_execution_time_ms': workflow_stats.max_execution_time or 0,
                        'min_execution_time_ms': workflow_stats.min_execution_time or 0,
                        'avg_final_score': float(workflow_stats.avg_final_score or 0),
                        'avg_iterations': float(workflow_stats.avg_iterations or 0)
                    },
                    'agent_statistics': [
                        {
                            'agent_name': stat.agent_name,
                            'total_executions': stat.total_executions,
                            'avg_execution_time_ms': float(stat.avg_execution_time or 0),
                            'successful_executions': stat.successful_executions,
                            'success_rate': (stat.successful_executions / stat.total_executions * 100) 
                                          if stat.total_executions > 0 else 0
                        }
                        for stat in agent_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to collect workflow metrics: {e}")
            return {'error': str(e)}
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all performance metrics"""
        logger.info("Collecting comprehensive performance metrics...")
        
        metrics = {
            'collection_time': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - self.start_time
        }
        
        # Collect system metrics
        metrics['system'] = self.collect_system_metrics()
        
        # Collect database metrics
        metrics['database'] = self.collect_database_metrics()
        
        # Collect LLM metrics
        metrics['llm'] = await self.collect_llm_metrics()
        
        # Collect workflow metrics
        metrics['workflow'] = self.collect_workflow_metrics()
        
        return metrics
    
    def analyze_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics and generate alerts"""
        alerts = []
        recommendations = []
        
        # Analyze system metrics
        if 'system' in metrics and 'error' not in metrics['system']:
            system = metrics['system']
            
            # CPU analysis
            cpu_percent = system.get('cpu', {}).get('percent', 0)
            if cpu_percent > self.alert_thresholds['cpu_usage_critical']:
                alerts.append({
                    'level': 'critical',
                    'component': 'system',
                    'metric': 'cpu_usage',
                    'value': cpu_percent,
                    'threshold': self.alert_thresholds['cpu_usage_critical'],
                    'message': f'Critical CPU usage: {cpu_percent:.1f}%'
                })
            elif cpu_percent > self.alert_thresholds['cpu_usage_warning']:
                alerts.append({
                    'level': 'warning',
                    'component': 'system',
                    'metric': 'cpu_usage',
                    'value': cpu_percent,
                    'threshold': self.alert_thresholds['cpu_usage_warning'],
                    'message': f'High CPU usage: {cpu_percent:.1f}%'
                })
            
            # Memory analysis
            memory_percent = system.get('memory', {}).get('percent', 0)
            if memory_percent > self.alert_thresholds['memory_usage_critical']:
                alerts.append({
                    'level': 'critical',
                    'component': 'system',
                    'metric': 'memory_usage',
                    'value': memory_percent,
                    'threshold': self.alert_thresholds['memory_usage_critical'],
                    'message': f'Critical memory usage: {memory_percent:.1f}%'
                })
            elif memory_percent > self.alert_thresholds['memory_usage_warning']:
                alerts.append({
                    'level': 'warning',
                    'component': 'system',
                    'metric': 'memory_usage',
                    'value': memory_percent,
                    'threshold': self.alert_thresholds['memory_usage_warning'],
                    'message': f'High memory usage: {memory_percent:.1f}%'
                })
        
        # Analyze database metrics
        if 'database' in metrics and 'error' not in metrics['database']:
            db = metrics['database']
            
            # Connection pool analysis
            pool_stats = db.get('connection_pool', {}).get('sync_pool', {})
            if pool_stats:
                checked_out = pool_stats.get('checked_out', 0)
                size = pool_stats.get('size', 0)
                if size > 0 and (checked_out / size) > 0.8:
                    alerts.append({
                        'level': 'warning',
                        'component': 'database',
                        'metric': 'connection_pool_usage',
                        'value': (checked_out / size) * 100,
                        'message': f'High connection pool usage: {checked_out}/{size} connections'
                    })
            
            # Query performance analysis
            query_perf = db.get('query_performance', {})
            avg_query_time = query_perf.get('avg_query_time', 0)
            if avg_query_time > 1.0:  # 1 second
                alerts.append({
                    'level': 'warning',
                    'component': 'database',
                    'metric': 'avg_query_time',
                    'value': avg_query_time,
                    'message': f'Slow average query time: {avg_query_time:.3f}s'
                })
        
        # Analyze workflow metrics
        if 'workflow' in metrics and 'error' not in metrics['workflow']:
            workflow = metrics['workflow']
            
            # Workflow execution time analysis
            workflow_stats = workflow.get('workflow_statistics', {})
            avg_exec_time = workflow_stats.get('avg_execution_time_ms', 0)
            if avg_exec_time > self.alert_thresholds['workflow_time_critical']:
                alerts.append({
                    'level': 'critical',
                    'component': 'workflow',
                    'metric': 'avg_execution_time',
                    'value': avg_exec_time,
                    'threshold': self.alert_thresholds['workflow_time_critical'],
                    'message': f'Critical workflow execution time: {avg_exec_time:.0f}ms'
                })
            elif avg_exec_time > self.alert_thresholds['workflow_time_warning']:
                alerts.append({
                    'level': 'warning',
                    'component': 'workflow',
                    'metric': 'avg_execution_time',
                    'value': avg_exec_time,
                    'threshold': self.alert_thresholds['workflow_time_warning'],
                    'message': f'Slow workflow execution time: {avg_exec_time:.0f}ms'
                })
            
            # Agent success rate analysis
            agent_stats = workflow.get('agent_statistics', [])
            for agent_stat in agent_stats:
                success_rate = agent_stat.get('success_rate', 100)
                if success_rate < 90:
                    alerts.append({
                        'level': 'warning',
                        'component': 'workflow',
                        'metric': 'agent_success_rate',
                        'value': success_rate,
                        'agent': agent_stat.get('agent_name'),
                        'message': f'Low success rate for {agent_stat.get("agent_name")}: {success_rate:.1f}%'
                    })
        
        # Generate recommendations
        if cpu_percent > 60:
            recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")
        
        if memory_percent > 60:
            recommendations.append("Monitor memory usage and consider increasing available RAM")
        
        if avg_query_time > 0.5:
            recommendations.append("Review database queries and consider adding indexes")
        
        cache_hit_rate = metrics.get('database', {}).get('query_performance', {}).get('cache_hit_rate', 0)
        if cache_hit_rate < 0.7:
            recommendations.append("Low cache hit rate - consider increasing cache size or TTL")
        
        return {
            'analysis_time': datetime.utcnow().isoformat(),
            'alerts': alerts,
            'recommendations': recommendations,
            'summary': {
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a['level'] == 'critical']),
                'warning_alerts': len([a for a in alerts if a['level'] == 'warning']),
                'health_status': 'critical' if any(a['level'] == 'critical' for a in alerts) 
                               else 'warning' if alerts else 'healthy'
            }
        }
    
    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a complete monitoring cycle"""
        try:
            # Collect metrics
            metrics = await self.collect_all_metrics()
            
            # Analyze performance
            analysis = self.analyze_performance(metrics)
            
            # Combine results
            result = {
                'monitoring_cycle': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'duration_seconds': time.time() - self.start_time
                },
                'metrics': metrics,
                'analysis': analysis
            }
            
            # Store in history
            self.metrics_history.append(result)
            
            # Keep only last 100 entries
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
            
            return result
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate performance report"""
        if not self.metrics_history:
            return "No metrics data available"
        
        latest = self.metrics_history[-1]
        
        report = f"""
Event Planning Agent v2 - Performance Report
Generated: {datetime.utcnow().isoformat()}
Monitoring Duration: {time.time() - self.start_time:.0f} seconds

=== SYSTEM HEALTH ===
Status: {latest.get('analysis', {}).get('summary', {}).get('health_status', 'unknown')}
Total Alerts: {latest.get('analysis', {}).get('summary', {}).get('total_alerts', 0)}
Critical Alerts: {latest.get('analysis', {}).get('summary', {}).get('critical_alerts', 0)}

=== SYSTEM METRICS ===
CPU Usage: {latest.get('metrics', {}).get('system', {}).get('cpu', {}).get('percent', 0):.1f}%
Memory Usage: {latest.get('metrics', {}).get('system', {}).get('memory', {}).get('percent', 0):.1f}%
Disk Usage: {latest.get('metrics', {}).get('system', {}).get('disk', {}).get('percent', 0):.1f}%

=== DATABASE PERFORMANCE ===
Query Cache Hit Rate: {latest.get('metrics', {}).get('database', {}).get('query_performance', {}).get('cache_hit_rate', 0):.1%}
Average Query Time: {latest.get('metrics', {}).get('database', {}).get('query_performance', {}).get('avg_query_time', 0):.3f}s
Total Queries: {latest.get('metrics', {}).get('database', {}).get('query_performance', {}).get('total_queries', 0)}

=== LLM PERFORMANCE ===
Cache Hit Rate: {latest.get('metrics', {}).get('llm', {}).get('llm_performance', {}).get('cache_hit_rate', 0):.1%}
Average Execution Time: {latest.get('metrics', {}).get('llm', {}).get('llm_performance', {}).get('avg_execution_time', 0):.3f}s
Total Requests: {latest.get('metrics', {}).get('llm', {}).get('llm_performance', {}).get('total_requests', 0)}

=== WORKFLOW PERFORMANCE ===
Average Execution Time: {latest.get('metrics', {}).get('workflow', {}).get('workflow_statistics', {}).get('avg_execution_time_ms', 0):.0f}ms
Average Final Score: {latest.get('metrics', {}).get('workflow', {}).get('workflow_statistics', {}).get('avg_final_score', 0):.3f}
Total Workflows (24h): {latest.get('metrics', {}).get('workflow', {}).get('workflow_statistics', {}).get('total_workflows', 0)}

=== ALERTS ===
"""
        
        alerts = latest.get('analysis', {}).get('alerts', [])
        if alerts:
            for alert in alerts:
                report += f"[{alert['level'].upper()}] {alert['component']}: {alert['message']}\n"
        else:
            report += "No active alerts\n"
        
        report += "\n=== RECOMMENDATIONS ===\n"
        recommendations = latest.get('analysis', {}).get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                report += f"- {rec}\n"
        else:
            report += "No recommendations at this time\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            logger.info(f"Performance report saved to {output_file}")
        
        return report


async def main():
    """Main monitoring function"""
    parser = argparse.ArgumentParser(description='Event Planning Agent v2 Performance Monitor')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--duration', type=int, default=0, help='Monitoring duration in seconds (0 = infinite)')
    parser.add_argument('--output', type=str, help='Output file for reports')
    parser.add_argument('--single', action='store_true', help='Run single monitoring cycle and exit')
    parser.add_argument('--report', action='store_true', help='Generate report and exit')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = PerformanceMonitor()
    
    if args.single:
        # Run single monitoring cycle
        result = await monitor.run_monitoring_cycle()
        print(json.dumps(result, indent=2))
        return
    
    if args.report:
        # Generate report from existing data
        report = monitor.generate_report(args.output)
        print(report)
        return
    
    # Continuous monitoring
    logger.info(f"Starting performance monitoring (interval: {args.interval}s)")
    
    start_time = time.time()
    cycle_count = 0
    
    try:
        while True:
            cycle_start = time.time()
            
            # Run monitoring cycle
            result = await monitor.run_monitoring_cycle()
            cycle_count += 1
            
            # Log summary
            analysis = result.get('analysis', {})
            summary = analysis.get('summary', {})
            health_status = summary.get('health_status', 'unknown')
            alert_count = summary.get('total_alerts', 0)
            
            logger.info(f"Cycle {cycle_count}: Health={health_status}, Alerts={alert_count}")
            
            # Print alerts if any
            alerts = analysis.get('alerts', [])
            for alert in alerts:
                if alert['level'] == 'critical':
                    logger.error(f"CRITICAL: {alert['message']}")
                else:
                    logger.warning(f"WARNING: {alert['message']}")
            
            # Generate periodic report
            if cycle_count % 10 == 0:  # Every 10 cycles
                report = monitor.generate_report(args.output)
                if not args.output:
                    print("\n" + "="*80)
                    print(report)
                    print("="*80 + "\n")
            
            # Check duration limit
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                logger.info(f"Monitoring duration limit reached ({args.duration}s)")
                break
            
            # Wait for next cycle
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, args.interval - cycle_duration)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise
    
    # Final report
    final_report = monitor.generate_report(args.output)
    logger.info("Final performance report generated")
    if not args.output:
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80)
        print(final_report)


if __name__ == '__main__':
    asyncio.run(main())