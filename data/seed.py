#!/usr/bin/env python3
"""
Database seed script for AI Tutor.
Run this once after migrations to populate the database with exercises, quizzes, and surveys.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.config import settings
from backend.database import Base, engine, SessionLocal
from backend.models import (
    Exercise,
    Quiz,
    QuizQuestion,
    Survey,
    SurveyQuestion,
)

QUIZZES_DATA = [
    {
        "id": "quiz_python_basics_pre",
        "title": "Python Basics Pre-Assessment",
        "description": "Test your knowledge of Python fundamentals before starting the course.",
        "quiz_type": "pre",
        "topic": "python",
        "questions": [
            {"question_number": 1, "question_text": "What will be the output of print(type(5 / 2))?", "question_type": "multiple_choice", "options": ["int", "float", "str", "double"], "correct_answer": "float", "explanation": "In Python 3, the / operator always returns a float.", "points": 1},
            {"question_number": 2, "question_text": "Which of the following is used to define a function in Python?", "question_type": "multiple_choice", "options": ["function", "def", "func", "define"], "correct_answer": "def", "explanation": "The 'def' keyword is used to define functions.", "points": 1},
            {"question_number": 3, "question_text": "What is the correct way to create a list containing 1-5?", "question_type": "multiple_choice", "options": ["[1, 2, 3, 4, 5]", "(1, 2, 3, 4, 5)", "{1, 2, 3, 4, 5}", "<1, 2, 3, 4, 5>"], "correct_answer": "[1, 2, 3, 4, 5]", "explanation": "Lists use square brackets.", "points": 1},
            {"question_number": 4, "question_text": "What does the modulo operator (%) return?", "question_type": "multiple_choice", "options": ["The quotient", "The remainder", "The product", "The difference"], "correct_answer": "The remainder", "explanation": "Modulo returns the remainder.", "points": 1},
            {"question_number": 5, "question_text": "What keyword starts a conditional statement?", "question_type": "short_answer", "options": None, "correct_answer": "if", "explanation": "The 'if' keyword starts conditionals.", "points": 1},
        ],
    },
    {
        "id": "quiz_python_basics_post",
        "title": "Python Basics Post-Assessment",
        "description": "Test your knowledge after completing the course.",
        "quiz_type": "post",
        "topic": "python",
        "questions": [
            {"question_number": 1, "question_text": "What will 'Hello World'[6:11] output?", "question_type": "multiple_choice", "options": ["Hello", "World", "lo Wo", "Error"], "correct_answer": "World", "explanation": "Slicing [6:11] extracts 'World'.", "points": 1},
            {"question_number": 2, "question_text": "What is [x*2 for x in range(3)]?", "question_type": "multiple_choice", "options": ["[0, 2, 4]", "[1, 2, 3]", "[2, 4, 6]", "[3, 6, 9]"], "correct_answer": "[0, 2, 4]", "explanation": "List comprehension creates [0, 2, 4].", "points": 1},
            {"question_number": 3, "question_text": "How do you define a default parameter?", "question_type": "multiple_choice", "options": ["def func(x = 5):", "def func(x: 5):", "def func(default x):", "func(x=5):"], "correct_answer": "def func(x = 5):", "explanation": "Default params use assignment in signature.", "points": 1},
            {"question_number": 4, "question_text": "What is 'hello'.upper().replace('L', 'X')?", "question_type": "multiple_choice", "options": ["HELLO", "HEXXO", "HELXO", "hELLO"], "correct_answer": "HEXXO", "explanation": "First upper(), then replace.", "points": 1},
            {"question_number": 5, "question_text": "What method adds to end of a list?", "question_type": "short_answer", "options": None, "correct_answer": "append", "explanation": "append() adds to the end.", "points": 1},
        ],
    },
]

SURVEYS_DATA = [
    {
        "id": "survey_learning_experience",
        "title": "Learning Experience Survey",
        "description": "Help us understand your learning experience.",
        "survey_type": "likert",
        "topic": "general",
        "questions": [
            {"question_number": 1, "question_text": "The AI Tutor helped me understand concepts better.", "question_category": "engagement", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 2, "question_text": "The hint system was helpful when I got stuck.", "question_category": "engagement", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 3, "question_text": "The exercises were appropriately challenging.", "question_category": "difficulty", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 4, "question_text": "I felt confident submitting my code.", "question_category": "confidence", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 5, "question_text": "The UI was intuitive and easy to navigate.", "question_category": "engagement", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
        ],
    },
    {
        "id": "survey_topic_feedback",
        "title": "Topic Feedback Survey",
        "description": "Provide feedback on specific topics.",
        "survey_type": "feedback",
        "topic": "general",
        "questions": [
            {"question_number": 1, "question_text": "How satisfied are you with the topics covered?", "question_category": "satisfaction", "scale_min": 1, "scale_max": 5, "scale_min_label": "Very Dissatisfied", "scale_max_label": "Very Satisfied", "is_required": True},
            {"question_number": 2, "question_text": "The exercises covered the topic material well.", "question_category": "relevance", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 3, "question_text": "I would recommend this platform to others.", "question_category": "recommendation", "scale_min": 1, "scale_max": 5, "scale_min_label": "Definitely Not", "scale_max_label": "Definitely Yes", "is_required": True},
        ],
    },
    {
        "id": "survey_diagnostic",
        "title": "Learning Diagnostic Survey",
        "description": "Help us identify your learning needs.",
        "survey_type": "likert",
        "topic": "diagnostic",
        "questions": [
            {"question_number": 1, "question_text": "I prefer hands-on practice over reading.", "question_category": "learning_style", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 2, "question_text": "I feel comfortable making mistakes while learning.", "question_category": "mindset", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 3, "question_text": "Immediate feedback helped me learn faster.", "question_category": "feedback", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
            {"question_number": 4, "question_text": "Hints reduced my frustration when stuck.", "question_category": "support", "scale_min": 1, "scale_max": 5, "scale_min_label": "Strongly Disagree", "scale_max_label": "Strongly Agree", "is_required": True},
        ],
    },
]


async def seed_all():
    """Seed all data."""
    exercises_file = Path(__file__).parent / "exercises.json"
    with open(exercises_file, "r", encoding="utf-8") as f:
        exercises_data = json.load(f)

    print(f"Loaded {len(exercises_data)} exercises from {exercises_file}")

    async with SessionLocal() as db:
        # Seed exercises
        for ex_data in exercises_data:
            result = await db.execute(select(Exercise).where(Exercise.id == ex_data["id"]))
            existing = result.scalar_one_or_none()

            if existing:
                continue

            exercise = Exercise(
                id=ex_data["id"],
                topic=ex_data["topic"],
                subtopic=ex_data.get("subtopic"),
                title=ex_data["title"],
                difficulty=ex_data.get("difficulty"),
                problem_statement=ex_data["problem_statement"],
                hint_l1=ex_data["hint_l1"],
                hint_l2=ex_data["hint_l2"],
                llm_context=ex_data["llm_context"],
                concept=ex_data["concept"],
                correct_criteria=ex_data["correct_criteria"],
                prerequisite_ids=ex_data.get("prerequisite_ids"),
                common_mistakes=ex_data.get("common_mistakes"),
                tags=ex_data.get("tags"),
            )
            db.add(exercise)
            print(f"  Added {ex_data['id']}: {ex_data['title']}")

        await db.commit()
        print("\nExercises seeding complete!")

        # Seed quizzes
        print("\n--- Seeding Quizzes ---")
        for quiz_data in QUIZZES_DATA:
            result = await db.execute(select(Quiz).where(Quiz.id == quiz_data["id"]))
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  Skipping {quiz_data['id']} (already exists)")
                continue

            quiz = Quiz(
                id=quiz_data["id"],
                title=quiz_data["title"],
                description=quiz_data.get("description"),
                quiz_type=quiz_data["quiz_type"],
                topic=quiz_data.get("topic"),
            )
            db.add(quiz)
            print(f"  Added quiz: {quiz_data['title']}")

            for q_data in quiz_data.get("questions", []):
                question = QuizQuestion(
                    quiz_id=quiz_data["id"],
                    question_number=q_data["question_number"],
                    question_text=q_data["question_text"],
                    question_type=q_data["question_type"],
                    options=q_data.get("options"),
                    correct_answer=q_data["correct_answer"],
                    explanation=q_data.get("explanation"),
                    points=q_data.get("points", 1),
                )
                db.add(question)

        await db.commit()
        print("Quizzes seeding complete!")

        # Seed surveys
        print("\n--- Seeding Surveys ---")
        for survey_data in SURVEYS_DATA:
            result = await db.execute(select(Survey).where(Survey.id == survey_data["id"]))
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  Skipping {survey_data['id']} (already exists)")
                continue

            survey = Survey(
                id=survey_data["id"],
                title=survey_data["title"],
                description=survey_data.get("description"),
                survey_type=survey_data["survey_type"],
                topic=survey_data.get("topic"),
            )
            db.add(survey)
            print(f"  Added survey: {survey_data['title']}")

            for q_data in survey_data.get("questions", []):
                question = SurveyQuestion(
                    survey_id=survey_data["id"],
                    question_number=q_data["question_number"],
                    question_text=q_data["question_text"],
                    question_category=q_data.get("question_category"),
                    scale_min=q_data.get("scale_min", 1),
                    scale_max=q_data.get("scale_max", 5),
                    scale_min_label=q_data.get("scale_min_label"),
                    scale_max_label=q_data.get("scale_max_label"),
                    is_required=q_data.get("is_required", True),
                )
                db.add(question)

        await db.commit()
        print("Surveys seeding complete!")

        # Verify
        result = await db.execute(select(Exercise))
        exercises = result.scalars().all()
        print(f"\nVerification: {len(exercises)} exercises in database")

        result = await db.execute(select(Quiz))
        quizzes = result.scalars().all()
        print(f"Verification: {len(quizzes)} quizzes in database")

        result = await db.execute(select(Survey))
        surveys = result.scalars().all()
        print(f"Verification: {len(surveys)} surveys in database")


if __name__ == "__main__":
    asyncio.run(seed_all())
