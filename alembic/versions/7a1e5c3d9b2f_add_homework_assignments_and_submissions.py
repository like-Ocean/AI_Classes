"""Add homework assignments and submissions

Revision ID: 7a1e5c3d9b2f
Revises: 4d11f65a8c2e
Create Date: 2026-04-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1e5c3d9b2f'
down_revision: Union[str, Sequence[str], None] = '4d11f65a8c2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'homework_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('allowed_formats', sa.JSON(), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_homework_assignments_course_id'), 'homework_assignments', ['course_id'], unique=False)
    op.create_index(op.f('ix_homework_assignments_module_id'), 'homework_assignments', ['module_id'], unique=False)
    op.create_index(op.f('ix_homework_assignments_material_id'), 'homework_assignments', ['material_id'], unique=False)
    op.create_index(op.f('ix_homework_assignments_created_by'), 'homework_assignments', ['created_by'], unique=False)

    op.create_table(
        'homework_submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('text_answer', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['homework_assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'student_id', name='uq_homework_submission_assignment_student')
    )
    op.create_index(op.f('ix_homework_submissions_assignment_id'), 'homework_submissions', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_homework_submissions_student_id'), 'homework_submissions', ['student_id'], unique=False)

    op.create_table(
        'homework_submission_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['homework_submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', 'file_id', name='uq_homework_submission_file')
    )
    op.create_index(op.f('ix_homework_submission_files_submission_id'), 'homework_submission_files', ['submission_id'], unique=False)
    op.create_index(op.f('ix_homework_submission_files_file_id'), 'homework_submission_files', ['file_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_homework_submission_files_file_id'), table_name='homework_submission_files')
    op.drop_index(op.f('ix_homework_submission_files_submission_id'), table_name='homework_submission_files')
    op.drop_table('homework_submission_files')

    op.drop_index(op.f('ix_homework_submissions_student_id'), table_name='homework_submissions')
    op.drop_index(op.f('ix_homework_submissions_assignment_id'), table_name='homework_submissions')
    op.drop_table('homework_submissions')

    op.drop_index(op.f('ix_homework_assignments_created_by'), table_name='homework_assignments')
    op.drop_index(op.f('ix_homework_assignments_material_id'), table_name='homework_assignments')
    op.drop_index(op.f('ix_homework_assignments_module_id'), table_name='homework_assignments')
    op.drop_index(op.f('ix_homework_assignments_course_id'), table_name='homework_assignments')
    op.drop_table('homework_assignments')
