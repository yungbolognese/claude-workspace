#!/usr/bin/env python3
"""
Helper script to approve proposals and generate implementation files
"""

import sys
import json
from pathlib import Path
from meta_agent import MetaAgent

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 approve_proposal.py <proposal-id>")
        print("\nAvailable proposals:")
        agent = MetaAgent()
        proposals = agent.proposer.load_pending_proposals()
        for p in proposals:
            print(f"  {p['id']}: {p['name']}")
        sys.exit(1)

    proposal_id = sys.argv[1]
    agent = MetaAgent()

    # Get proposal details
    proposal = agent.get_proposal(proposal_id)
    if not proposal:
        print(f"Error: Proposal '{proposal_id}' not found")
        sys.exit(1)

    # Show proposal summary
    print(f"\n=== Approving Proposal ===")
    print(f"Name: {proposal['name']}")
    print(f"Type: {proposal['type']}")
    print(f"Impact: {proposal['impact']['total_time_saved_estimate']}")
    print(f"Usage: {proposal['usage_example']}\n")

    # Ask for confirmation if interactive
    if sys.stdin.isatty():
        response = input("Approve and generate implementation? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            sys.exit(0)

    # Approve and implement
    result = agent.approve_proposal(proposal_id)

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)

    print(f"\n✓ Proposal approved and implemented!")
    print(f"Status: {result['status']}")
    print(f"Type: {result['type']}")

    if "script_path" in result:
        print(f"Script: {result['script_path']}")
    if "template_path" in result:
        print(f"Template: {result['template_path']}")

    print(f"\nNext steps:")
    print(f"  {result['next_steps']}")

    # Move proposal to approved
    proposal_file = Path(agent.base_dir) / "proposals" / f"{proposal_id}.json"
    if proposal_file.exists():
        approved_dir = Path(agent.base_dir) / "proposals" / "approved"
        approved_dir.mkdir(exist_ok=True)
        proposal_file.rename(approved_dir / f"{proposal_id}.json")
        print(f"\nProposal moved to approved/")

if __name__ == "__main__":
    main()
