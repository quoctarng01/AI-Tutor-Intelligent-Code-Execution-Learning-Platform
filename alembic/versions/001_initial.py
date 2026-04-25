"""Initial schema: exercises, sessions, attempts, hint_state, hint_logs

Revision ID: 001_initial
Revises:
Create Date: 2026-04-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # exercises table
    op.create_table(
        'exercises',
        sa.Column('id', sa.String(20), primary_key=True),
        sa.Column('topic', sa.String(50), nullable=False),
        sa.Column('subtopic', sa.String(50), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('difficulty', sa.SmallInteger, nullable=True),
        sa.Column('problem_statement', sa.Text, nullable=False),
        sa.Column('hint_l1', sa.Text, nullable=False),
        sa.Column('hint_l2', sa.Text, nullable=False),
        sa.Column('llm_context', sa.Text, nullable=False),
        sa.Column('concept', sa.String(200), nullable=False),
        sa.Column('correct_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('prerequisite_ids', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('common_mistakes', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.CheckConstraint('difficulty BETWEEN 1 AND 5', name='ck_exercises_difficulty_range'),
    )

    # sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('group_type', sa.String(10), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("group_type IN ('tutor','control')", name='ck_sessions_group_type'),
    )

    # hint_state table
    op.create_table(
        'hint_state',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id'), primary_key=True),
        sa.Column('exercise_id', sa.String(20), sa.ForeignKey('exercises.id'), primary_key=True),
        sa.Column('current_level', sa.SmallInteger, server_default=sa.text('0'), nullable=False),
        sa.Column('is_solved', sa.Boolean, server_default=sa.text('FALSE'), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # attempts table
    op.create_table(
        'attempts',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('exercise_id', sa.String(20), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('submitted_code', sa.Text, nullable=False),
        sa.Column('is_correct', sa.Boolean, nullable=False),
        sa.Column('hints_used', sa.SmallInteger, server_default=sa.text('0'), nullable=False),
        sa.Column('time_to_solve_s', sa.Integer, nullable=True),
        sa.Column('hint_state', sa.String(20), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # hint_logs table
    op.create_table(
        'hint_logs',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id'), nullable=False),
        sa.Column('exercise_id', sa.String(20), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('hint_level', sa.SmallInteger, nullable=False),
        sa.Column('prompt_version', sa.String(20), nullable=False),
        sa.Column('prompt_rendered', sa.Text, nullable=False),
        sa.Column('llm_response', sa.Text, nullable=False),
        sa.Column('was_pre_authored', sa.Boolean, server_default=sa.text('FALSE'), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('hint_logs')
    op.drop_table('attempts')
    op.drop_table('hint_state')
    op.drop_table('sessions')
    op.drop_table('exercises')
