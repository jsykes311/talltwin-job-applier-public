import os
import sys
import json
import argparse
from typing import Dict, Any

# Ensure src module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db import Database
from src.scraper import GreenhouseScraper, LeverScraper, RemoteOKScraper
from src.ai import JobEvaluator
from src.automator import GreenhouseApplier, LeverApplier

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CRITERIA_PATH = os.path.join(BASE_DIR, "config", "criteria.json")
PROFILE_PATH = os.path.join(BASE_DIR, "config", "user_profile.json")

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def run_discover(db: Database, criteria: Dict[str, Any]):
    print("🔍 Discovering jobs across job boards...")
    scrapers = [
        GreenhouseScraper(criteria),
        LeverScraper(criteria),
        RemoteOKScraper(criteria)
    ]
    
    total_found = 0
    for scraper in scrapers:
        name = scraper.__class__.__name__
        print(f"Running {name}...")
        jobs = scraper.fetch_jobs()
        print(f"Found {len(jobs)} postings via {name}.")
        for j in jobs:
            db.insert_job(j)
            total_found += 1

    print(f"✅ Discovery complete! Processed {total_found} postings.")

def run_evaluate(db: Database, criteria: Dict[str, Any], profile: Dict[str, Any]):
    print("🧠 Evaluating discovered jobs...")
    jobs = db.get_jobs(status="DISCOVERED")
    if not jobs:
        print("No un-evaluated 'DISCOVERED' jobs found.")
        return

    evaluator = JobEvaluator(criteria, profile)
    threshold = criteria.get("match_score_threshold", 70)
    matched_cnt = 0
    rejected_cnt = 0

    for j in jobs:
        score, reason = evaluator.evaluate_job(j["title"], j.get("description", ""))
        status = "MATCHED" if score >= threshold else "REJECTED"
        db.update_job_status(j["id"], status=status, match_score=score, match_reason=reason)
        if status == "MATCHED":
            matched_cnt += 1
            print(f"  [MATCH {score:.1f}%] {j['title']} @ {j['company']} ({j['platform']})")
        else:
            rejected_cnt += 1

    print(f"✅ Evaluation complete! Matched: {matched_cnt}, Rejected: {rejected_cnt}")

def run_apply(db: Database, profile: Dict[str, Any], mode: str = "dry_run", limit: int = 5):
    print(f"🚀 Running Application Automator in [{mode.upper()}] mode (Limit: {limit})...")
    matched_jobs = db.get_jobs(status="MATCHED")[:limit]
    if not matched_jobs:
        print("No 'MATCHED' jobs ready for application.")
        return

    gh_applier = GreenhouseApplier(profile, db, mode=mode)
    lever_applier = LeverApplier(profile, db, mode=mode)

    applied_count = 0
    for j in matched_jobs:
        platform = j["platform"]
        print(f"\nApplying to: {j['title']} @ {j['company']} [{platform}]")
        
        success = False
        if platform == "greenhouse":
            success = gh_applier.apply(j)
        elif platform == "lever":
            success = lever_applier.apply(j)
        else:
            print(f"  Skipping unsupported platform '{platform}' URL: {j['url']}")
            continue

        if success:
            applied_count += 1

    print(f"\n✅ Application run finished! Processed {applied_count} jobs.")

def print_stats(db: Database):
    stats = db.get_stats()
    print("\n📊 Application Database Summary:")
    print("-" * 35)
    for k, v in stats.items():
        print(f"  {k:<12}: {v}")
    print("-" * 35)

def main():
    parser = argparse.ArgumentParser(description="Autonomous Job Application Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("discover", help="Fetch job postings from supported ATS boards & APIs")
    subparsers.add_parser("evaluate", help="Score discovered job postings using AI match rules")
    
    apply_parser = subparsers.add_parser("apply", help="Run automated job application submitter")
    apply_parser.add_argument("--mode", choices=["dry_run", "review", "autonomous"], default="dry_run",
                              help="Execution mode (default: dry_run)")
    apply_parser.add_argument("--limit", type=int, default=5, help="Max applications to run")

    subparsers.add_parser("stats", help="Show database summary metrics")

    all_parser = subparsers.add_parser("all", help="Run discover, evaluate, and apply in sequence")
    all_parser.add_argument("--mode", choices=["dry_run", "review", "autonomous"], default="dry_run")
    all_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    db = Database()
    criteria = load_json(CRITERIA_PATH)
    profile = load_json(PROFILE_PATH)

    if args.command == "discover":
        run_discover(db, criteria)
    elif args.command == "evaluate":
        run_evaluate(db, criteria, profile)
    elif args.command == "apply":
        run_apply(db, profile, mode=args.mode, limit=args.limit)
    elif args.command == "stats":
        print_stats(db)
    elif args.command == "all":
        run_discover(db, criteria)
        run_evaluate(db, criteria, profile)
        run_apply(db, profile, mode=args.mode, limit=args.limit)
        print_stats(db)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
