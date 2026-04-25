"""Add quiz and survey models

Revision ID: 002_add_quiz_survey
Revises: 001_initial
Create Date: 2026-04-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_quiz_survey'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Quiz tables
    op.create_table(
        'quizzes',
        sa.Column('id', sa.String(30), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('quiz_type', sa.String(20), nullable=False),
        sa.Column('topic', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='TRUE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("quiz_type IN ('pre','post')", name='ck_quizzes_quiz_type'),
    )

    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('quiz_id', sa.String(30), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.SmallInteger, nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False),
        sa.Column('options', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('correct_answer', sa.String(500), nullable=False),
        sa.Column('explanation', sa.Text, nullable=True),
        sa.Column('points', sa.SmallInteger, server_default='1', nullable=False),
        sa.CheckConstraint("question_type IN ('multiple_choice','short_answer')", name='ck_quiz_questions_type'),
        sa.CheckConstraint("points >= 0", name='ck_quiz_questions_points'),
    )

    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('quiz_id', sa.String(30), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float, server_default='0', nullable=False),
        sa.Column('max_score', sa.Float, server_default='0', nullable=False),
        sa.Column('is_completed', sa.Boolean, server_default='FALSE', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'quiz_responses',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('attempt_id', sa.BigInteger, sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.BigInteger, sa.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answer', sa.String(1000), nullable=False),
        sa.Column('is_correct', sa.Boolean, nullable=True),
        sa.Column('points_earned', sa.Float, server_default='0', nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # Survey tables
    op.create_table(
        'surveys',
        sa.Column('id', sa.String(30), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('survey_type', sa.String(50), nullable=False),
        sa.Column('topic', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='TRUE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'survey_questions',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('survey_id', sa.String(30), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_number', sa.SmallInteger, nullable=False),
        sa.Column('question_text', sa.Text, nullable=False),
        sa.Column('question_category', sa.String(50), nullable=True),
        sa.Column('scale_min', sa.SmallInteger, server_default='1', nullable=False),
        sa.Column('scale_max', sa.SmallInteger, server_default='5', nullable=False),
        sa.Column('scale_min_label', sa.String(100), nullable=True),
        sa.Column('scale_max_label', sa.String(100), nullable=True),
        sa.Column('is_required', sa.Boolean, server_default='TRUE', nullable=False),
    )

    op.create_table(
        'survey_responses',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('survey_id', sa.String(30), sa.ForeignKey('surveys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_complete', sa.Boolean, server_default='FALSE', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        'survey_answers',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('response_id', sa.BigInteger, sa.ForeignKey('survey_responses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.BigInteger, sa.ForeignKey('survey_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('value', sa.SmallInteger, nullable=False),
        sa.Column('text_response', sa.Text, nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # Create indexes for better query performance
    op.create_index('ix_quiz_attempts_session', 'quiz_attempts', ['session_id'])
    op.create_index('ix_quiz_attempts_quiz', 'quiz_attempts', ['quiz_id'])
    op.create_index('ix_quiz_responses_attempt', 'quiz_responses', ['attempt_id'])
    op.create_index('ix_survey_responses_session', 'survey_responses', ['session_id'])
    op.create_index('ix_survey_answers_response', 'survey_answers', ['response_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_survey_answers_response')
    op.drop_index('ix_survey_responses_session')
    op.drop_index('ix_quiz_responses_attempt')
    op.drop_index('ix_quiz_attempts_quiz')
    op.drop_index('ix_quiz_attempts_session')

    # Drop survey tables
    op.drop_table('survey_answers')
    op.drop_table('survey_responses')
    op.drop_table('survey_questions')
    op.drop_table('surveys')

    # Drop quiz tables
    op.drop_table('quiz_responses')
    op.drop_table('quiz_attempts')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
