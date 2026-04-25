#!/usr/bin/env python3
"""
Validation Log Analyzer for Thesis Research.

Analyzes the hint validation logs to provide insights for your thesis research.

Usage:
    python backend/scripts/analyze_validations.py
"""

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "logs" / "hint_validation.log"


def load_logs():
    """Load validation logs from file."""
    logs = []
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    return logs


def analyze_by_level(logs):
    """Analyze rejection patterns by hint level."""
    by_level = defaultdict(list)
    for log in logs:
        level = str(log.get("details", {}).get("level", "unknown"))
        by_level[level].append(log)
    
    print("\n" + "=" * 60)
    print("ANALYSIS BY HINT LEVEL")
    print("=" * 60)
    
    for level in sorted(by_level.keys()):
        level_logs = by_level[level]
        print(f"\nLevel {level}: {len(level_logs)} rejections")
        
        # Count reasons
        reasons = Counter(l.get("reason", "unknown") for l in level_logs)
        print("  Top rejection reasons:")
        for reason, count in reasons.most_common(5):
            print(f"    - {reason}: {count}")


def analyze_by_reason(logs):
    """Analyze rejection reasons in detail."""
    print("\n" + "=" * 60)
    print("REJECTION REASON ANALYSIS")
    print("=" * 60)
    
    reasons = Counter()
    for log in logs:
        reason = log.get("reason", "unknown")
        reasons[reason] += 1
    
    for reason, count in reasons.most_common():
        percentage = (count / len(logs)) * 100
        print(f"  {reason}: {count} ({percentage:.1f}%)")


def analyze_text_patterns(logs):
    """Analyze text patterns in rejected hints."""
    print("\n" + "=" * 60)
    print("TEXT PATTERN ANALYSIS")
    print("=" * 60)
    
    # Length distribution
    lengths = [l.get("details", {}).get("text_length", 0) for l in logs]
    if lengths:
        print(f"  Rejected text lengths:")
        print(f"    - Min: {min(lengths)} chars")
        print(f"    - Max: {max(lengths)} chars")
        print(f"    - Avg: {sum(lengths)/len(lengths):.1f} chars")
    
    # Text previews
    print("\n  Sample rejected hints:")
    for log in logs[:5]:
        preview = log.get("text_preview", "N/A")[:80]
        reason = log.get("reason", "unknown")
        print(f"    [{reason}] {preview}...")


def analyze_temporal_patterns(logs):
    """Analyze temporal patterns in rejections."""
    print("\n" + "=" * 60)
    print("TEMPORAL PATTERNS")
    print("=" * 60)
    
    # Group by hour
    by_hour = defaultdict(int)
    for log in logs:
        ts = log.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                by_hour[dt.strftime("%H:00")] += 1
            except ValueError:
                continue
    
    if by_hour:
        print("  Rejections by hour of day:")
        for hour in sorted(by_hour.keys()):
            count = by_hour[hour]
            bar = "#" * (count // 2)
            print(f"    {hour}: {bar} ({count})")


def generate_recommendations(logs):
    """Generate recommendations based on analysis."""
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS FOR LLM PROMPT OPTIMIZATION")
    print("=" * 60)
    
    reasons = Counter(l.get("reason", "unknown") for l in logs)
    total = len(logs)
    
    if total == 0:
        print("  No data yet. Collect more validation logs.")
        return
    
    recommendations = []
    
    # Check for common patterns
    if reasons.get("forbidden_words", 0) / total > 0.2:
        recommendations.append(
            "High rate of forbidden word usage. "
            "Consider adding explicit word restrictions to the LLM prompt."
        )
    
    if reasons.get("response_too_short", 0) / total > 0.1:
        recommendations.append(
            "Many responses too short. "
            "Consider requiring minimum length in the prompt or increasing max_tokens."
        )
    
    if reasons.get("irrelevant_response", 0) / total > 0.1:
        recommendations.append(
            "Irrelevant responses detected. "
            "Consider adding concept reinforcement to the LLM prompt."
        )
    
    if reasons.get("level_specific_violation", 0) / total > 0.15:
        recommendations.append(
            "Level-specific violations high. "
            "Consider refining the level-specific instructions in templates."
        )
    
    if not recommendations:
        recommendations.append(
            "Good overall performance. Continue monitoring for edge cases."
        )
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")


def main():
    print("\n" + "=" * 60)
    print("HINT VALIDATION LOG ANALYZER")
    print("=" * 60)
    print(f"\nLog file: {LOG_FILE}")
    
    logs = load_logs()
    print(f"Total entries loaded: {len(logs)}")
    
    if not logs:
        print("\nNo validation logs found. Run hint requests to generate data.")
        print("Logs are automatically created in: logs/hint_validation.log")
        return
    
    analyze_by_level(logs)
    analyze_by_reason(logs)
    analyze_text_patterns(logs)
    analyze_temporal_patterns(logs)
    generate_recommendations(logs)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
