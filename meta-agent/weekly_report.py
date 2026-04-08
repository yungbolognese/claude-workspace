#!/usr/bin/env python3
"""
Generate periodic reports for the meta-agent
Can be run manually or via cron job
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from meta_agent import MetaAgent

def main():
    agent = MetaAgent()

    # Check if we should generate a report
    last_report = agent.config.get("last_report")
    if last_report:
        last_report_date = datetime.fromisoformat(last_report)
        if datetime.now() - last_report_date < timedelta(days=7):
            print("Weekly report already generated this week")
            return

    # Run analysis
    print("Running pattern analysis...")
    result = agent.analyze_patterns()

    # Generate report
    print("\nGenerating weekly report...")
    report = agent.generate_report("markdown")

    # Save report
    reports_dir = agent.base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    report_file = reports_dir / f"weekly_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_file, 'w') as f:
        f.write(report)

    # Update config
    agent.config["last_report"] = datetime.now().isoformat()
    agent._save_config()

    print(f"\n✓ Report saved to: {report_file}")
    print(f"\nSummary:")
    print(f"  Patterns detected: {result['patterns_detected']}")
    print(f"  Proposals generated: {result['proposals_generated']}")

    # Print report to stdout
    print("\n" + "="*60)
    print(report)
    print("="*60)

if __name__ == "__main__":
    main()
