#!/usr/bin/env python3
"""
LiteLLM Usage Monitor Script
A simple script to query LiteLLM database directly and generate usage reports.
This works without Enterprise features and provides comprehensive usage analytics.
"""

import psycopg2
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

class LiteLLMUsageMonitor:
    def __init__(self, db_host="localhost", db_port=5432, db_name="litellm", 
                 db_user="postgres", db_password="litellm_password123"):
        """Initialize the LiteLLM usage monitor."""
        self.connection_params = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        
    def connect(self):
        """Connect to the PostgreSQL database."""
        try:
            return psycopg2.connect(**self.connection_params)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)
    
    def get_usage_summary(self, hours=24) -> Dict[str, Any]:
        """Get usage summary for the specified time period."""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            COUNT(*) as total_requests,
            SUM(COALESCE(spend, 0)) as total_cost,
            AVG(COALESCE(spend, 0)) as avg_cost_per_request,
            SUM(COALESCE(prompt_tokens, 0)) as total_prompt_tokens,
            SUM(COALESCE(completion_tokens, 0)) as total_completion_tokens,
            COUNT(DISTINCT "user") as unique_users,
            COUNT(DISTINCT api_key) as unique_api_keys,
            COUNT(CASE WHEN status != 'success' THEN 1 END) as error_count
        FROM "LiteLLM_SpendLogs" 
        WHERE "startTime" >= NOW() - INTERVAL '%s hours'
        """
        
        cursor.execute(query, (hours,))
        result = cursor.fetchone()
        
        summary = {
            'time_period_hours': hours,
            'total_requests': result[0] or 0,
            'total_cost_usd': float(result[1] or 0),
            'avg_cost_per_request_usd': float(result[2] or 0),
            'total_prompt_tokens': result[3] or 0,
            'total_completion_tokens': result[4] or 0,
            'unique_users': result[5] or 0,
            'unique_api_keys': result[6] or 0,
            'error_count': result[7] or 0,
            'success_rate_percent': round((1 - (result[7] or 0) / max(result[0] or 1, 1)) * 100, 2)
        }
        
        cursor.close()
        conn.close()
        return summary
    
    def get_usage_by_model(self, hours=24) -> List[Dict[str, Any]]:
        """Get usage breakdown by model."""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            COALESCE(model, 'unknown') as model,
            COUNT(*) as requests,
            SUM(COALESCE(spend, 0)) as total_cost,
            AVG(COALESCE(spend, 0)) as avg_cost,
            SUM(COALESCE(prompt_tokens, 0)) as prompt_tokens,
            SUM(COALESCE(completion_tokens, 0)) as completion_tokens,
            COUNT(CASE WHEN status != 'success' THEN 1 END) as errors,
            AVG(EXTRACT(EPOCH FROM ("endTime" - "startTime")) * 1000) as avg_response_time_ms
        FROM "LiteLLM_SpendLogs" 
        WHERE "startTime" >= NOW() - INTERVAL '%s hours'
          AND "endTime" IS NOT NULL
        GROUP BY model
        ORDER BY total_cost DESC
        """
        
        cursor.execute(query, (hours,))
        results = cursor.fetchall()
        
        models = []
        for row in results:
            models.append({
                'model': row[0],
                'requests': row[1],
                'total_cost_usd': float(row[2] or 0),
                'avg_cost_per_request_usd': float(row[3] or 0),
                'prompt_tokens': row[4] or 0,
                'completion_tokens': row[5] or 0,
                'error_count': row[6] or 0,
                'error_rate_percent': round((row[6] or 0) / max(row[1], 1) * 100, 2),
                'avg_response_time_ms': round(float(row[7] or 0), 2)
            })
        
        cursor.close()
        conn.close()
        return models
    
    def get_hourly_usage(self, hours=24) -> List[Dict[str, Any]]:
        """Get hourly usage breakdown."""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            DATE_TRUNC('hour', "startTime") as hour,
            COUNT(*) as requests,
            SUM(COALESCE(spend, 0)) as cost,
            COUNT(CASE WHEN status != 'success' THEN 1 END) as errors
        FROM "LiteLLM_SpendLogs" 
        WHERE "startTime" >= NOW() - INTERVAL '%s hours'
        GROUP BY DATE_TRUNC('hour', "startTime")
        ORDER BY hour DESC
        """
        
        cursor.execute(query, (hours,))
        results = cursor.fetchall()
        
        hourly_data = []
        for row in results:
            hourly_data.append({
                'hour': row[0].isoformat() if row[0] else None,
                'requests': row[1],
                'cost_usd': float(row[2] or 0),
                'error_count': row[3] or 0,
                'error_rate_percent': round((row[3] or 0) / max(row[1], 1) * 100, 2)
            })
        
        cursor.close()
        conn.close()
        return hourly_data
    
    def generate_report(self, hours=24, format='json') -> str:
        """Generate a comprehensive usage report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_usage_summary(hours),
            'by_model': self.get_usage_by_model(hours),
            'hourly_breakdown': self.get_hourly_usage(hours)
        }
        
        if format.lower() == 'json':
            return json.dumps(report, indent=2)
        elif format.lower() == 'text':
            return self._format_text_report(report)
        else:
            raise ValueError("Format must be 'json' or 'text'")
    
    def _format_text_report(self, report: Dict[str, Any]) -> str:
        """Format report as human-readable text."""
        summary = report['summary']
        
        text = f"""
LiteLLM Usage Report
Generated: {report['generated_at']}
Time Period: Last {summary['time_period_hours']} hours

=== SUMMARY ===
Total Requests: {summary['total_requests']:,}
Total Cost: ${summary['total_cost_usd']:.6f}
Average Cost per Request: ${summary['avg_cost_per_request_usd']:.6f}
Total Tokens: {summary['total_prompt_tokens'] + summary['total_completion_tokens']:,}
  - Prompt Tokens: {summary['total_prompt_tokens']:,}
  - Completion Tokens: {summary['total_completion_tokens']:,}
Unique Users: {summary['unique_users']}
Unique API Keys: {summary['unique_api_keys']}
Success Rate: {summary['success_rate_percent']}%
Errors: {summary['error_count']}

=== BY MODEL ===
"""
        
        for model in report['by_model']:
            text += f"""
Model: {model['model']}
  Requests: {model['requests']:,}
  Cost: ${model['total_cost_usd']:.6f}
  Avg Cost/Request: ${model['avg_cost_per_request_usd']:.6f}
  Tokens: {model['prompt_tokens'] + model['completion_tokens']:,}
  Avg Response Time: {model['avg_response_time_ms']:.1f}ms
  Error Rate: {model['error_rate_percent']}%
"""
        
        text += "\n=== HOURLY BREAKDOWN ===\n"
        for hour in report['hourly_breakdown'][:12]:  # Show last 12 hours
            text += f"{hour['hour']}: {hour['requests']} requests, ${hour['cost_usd']:.6f}, {hour['error_rate_percent']}% errors\n"
        
        return text

def main():
    parser = argparse.ArgumentParser(description='LiteLLM Usage Monitor')
    parser.add_argument('--hours', type=int, default=24, help='Time period in hours (default: 24)')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    monitor = LiteLLMUsageMonitor(
        db_host=args.host,
        db_port=args.port
    )
    
    try:
        report = monitor.generate_report(hours=args.hours, format=args.format)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)
            
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
