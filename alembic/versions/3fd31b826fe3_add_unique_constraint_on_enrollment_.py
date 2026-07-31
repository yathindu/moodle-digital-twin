"""add unique constraint on enrollment student+course

Revision ID: 3fd31b826fe3
Revises: a9cdda29a783
Create Date: 2026-07-31 11:38:43.225857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fd31b826fe3'
down_revision: Union[str, Sequence[str], None] = 'a9cdda29a783'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('enrollments') as batch_op:
        batch_op.create_unique_constraint('uq_enrollment_student_course', ['student_id', 'course_id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('enrollments') as batch_op:
        batch_op.drop_constraint('uq_enrollment_student_course', type_='unique')
