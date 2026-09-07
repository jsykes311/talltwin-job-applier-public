#!/usr/bin/env python3
"""
One-Touch Autonomous Job Application Engine
Runs Discovery -> Evaluation -> Auto-Apply in a single seamless execution.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.db import Database
from src.scraper import GreenhouseScraper, LeverScraper, RemoteOKScraper
from src.ai import JobEvaluator
from src.automator import GreenhouseApplier, LeverApplier

CRITERIA_PATH = os.path.join(BASE_DIR, "config", "criteria.json")
PROFILE_PATH = os.path.join(BASE_DIR, "config", "user_profile.json")

def load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def execute_one_touch(mode: str = "dry_run", limit: int = 5, min_score: float = 70.0, progress_callback=None):
    """
    Executes the full pipeline in one touch.
    - mode: 'dry_run', 'review', or 'autonomous'
    - limit: max applications to process in this run
    - min_score: minimum AI match score threshold to apply
    """
    db = Database()
    criteria = load_json(CRITERIA_PATH)
    profile = load_json(PROFILE_PATH)

    summary = {
        "discovered": 0,
        "matched": 0,
        "applied": 0,
        "failed": 0,
        "jobs_applied": []
    }

    # STEP 1: Discovery
    if progress_callback:
        progress_callback("🔍 Step 1/3: Discovering new job postings...", 0.1)
    else:
        print("\n⚡ STEP 1: Discovering new job postings across boards...")

    scrapers = [
        GreenhouseScraper(criteria),
        LeverScraper(criteria),
        RemoteOKScraper(criteria)
    ]
    
    for scraper in scrapers:
        try:
            jobs = scraper.fetch_jobs()
            for j in jobs:
                db.insert_job(j)
                summary["discovered"] += 1
        except Exception as e:
            print(f"Scraper error: {e}")

    # STEP 2: AI Match Scoring
    if progress_callback:
        progress_callback("🧠 Step 2/3: AI match evaluation & scoring...", 0.4)
    else:
        print("\n⚡ STEP 2: AI evaluating job descriptions against candidate profile...")

    discovered_jobs = db.get_jobs(status="DISCOVERED")
    evaluator = JobEvaluator(criteria, profile)
    
    for j in discovered_jobs:
        score, reason = evaluator.evaluate_job(j["title"], j.get("description", ""))
        status = "MATCHED" if score >= min_score else "REJECTED"
        db.update_job_status(j["id"], status=status, match_score=score, match_reason=reason)
        if status == "MATCHED":
            summary["matched"] += 1

    # STEP 3: Auto-Application
    if progress_callback:
        progress_callback(f"🚀 Step 3/3: Executing auto-applier in [{mode.upper()}] mode...", 0.7)
    else:
        print(f"\n⚡ STEP 3: Executing Auto-Applier in [{mode.upper()}] mode (Max: {limit})...")

    matched_jobs = db.get_jobs(status="MATCHED", min_score=min_score)[:limit]
    
    gh_applier = GreenhouseApplier(profile, db, mode=mode)
    lever_applier = LeverApplier(profile, db, mode=mode)

    for idx, j in enumerate(matched_jobs):
        if progress_callback:
            prog_val = 0.7 + (0.3 * ((idx + 1) / len(matched_jobs)))
            progress_callback(f"🚀 Applying to ({idx+1}/{len(matched_jobs)}): {j['title']} @ {j['company']}...", prog_val)
        
        platform = j["platform"]
        success = False
        if platform == "greenhouse":
            success = gh_applier.apply(j)
        elif platform == "lever":
            success = lever_applier.apply(j)
        
        if success:
            summary["applied"] += 1
            summary["jobs_applied"].append({
                "id": j["id"],
                "title": j["title"],
                "company": j["company"],
                "score": j["match_score"],
                "url": j["url"]
            })
        else:
            summary["failed"] += 1

    if progress_callback:
        progress_callback("✅ One-Touch Execution Completed!", 1.0)

    return summary

def main():
    parser = argparse.ArgumentParser(description="One-Touch Autonomous Job Applier")
    parser.add_argument("--mode", choices=["dry_run", "review", "autonomous"], default="dry_run",
                        help="Execution mode (default: dry_run)")
    parser.add_argument("--limit", type=int, default=5, help="Maximum jobs to auto-apply per run")
    parser.add_argument("--min-score", type=float, default=70.0, help="Minimum match score threshold")

    args = parser.parse_args()

    print("=====================================================")
    print("⚡ ONE-TOUCH AUTONOMOUS JOB APPLICATION RUNNER")
    print(f"   Mode: {args.mode.upper()} | Limit: {args.limit} | Min Score: {args.min_score}%")
    print("=====================================================")

    res = execute_one_touch(mode=args.mode, limit=args.limit, min_score=args.min_score)

    print("\n=====================================================")
    print("🎉 ONE-TOUCH RUN RESULTS")
    print("=====================================================")
    print(f"  🔍 Discovered Postings : {res['discovered']}")
    print(f"  🧠 High Matches Found : {res['matched']}")
    print(f"  🚀 Applications Processed: {res['applied']}")
    print(f"  ⚠️  Failed Applications : {res['failed']}")
    print("-----------------------------------------------------")
    if res["jobs_applied"]:
        print("Processed Jobs:")
        for job in res["jobs_applied"]:
            print(f"  • #{job['id']} {job['title']} @ {job['company']} (Match: {job['score']:.1f}%)")
            print(f"    URL: {job['url']}")
    print("=====================================================\n")

if __name__ == "__main__":
    main()
