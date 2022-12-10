"""Added email verification

Revision ID: fab6d861e8a6
Revises: f673d655d486
Create Date: 2022-02-10 20:18:01.729835

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fab6d861e8a6'
down_revision = 'f673d655d486'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'email_verified')
    # ### end Alembic commands ###
