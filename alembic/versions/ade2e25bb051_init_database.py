"""init database

Revision ID: ade2e25bb051
Revises: 
Create Date: 2023-10-16 19:20:08.228392

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ade2e25bb051'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    event_status = postgresql.ENUM('created', 'upcoming', 'ongoing', 'closed', 'completed', 'archived', 'cancelled',
                                   name='eventstatus', create_type=False)
    event_status.create(op.get_bind(), checkfirst=True)

    op.create_table('events',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=128), nullable=False),
                    sa.Column('status', event_status, nullable=False),
                    sa.Column('deadline', sa.DateTime(timezone=True), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_table('users',
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('email', sa.String(length=320), nullable=False),
                    sa.Column('hashed_password', sa.String(length=1024), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=False),
                    sa.Column('is_superuser', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    match_status = postgresql.ENUM('upcoming', 'ongoing', 'completed', name='matchstatus', create_type=False)
    match_status.create(op.get_bind(), checkfirst=True)

    op.create_table('matches',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('home_team', sa.String(length=128), nullable=False),
                    sa.Column('away_team', sa.String(length=128), nullable=False),
                    sa.Column('status', match_status, nullable=False),
                    sa.Column('home_goals', sa.Integer(), nullable=True),
                    sa.Column('away_goals', sa.Integer(), nullable=True),
                    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_matches_id'), 'matches', ['id'], unique=False)
    op.create_table('predictions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('home_goals', sa.Integer(), nullable=True),
                    sa.Column('away_goals', sa.Integer(), nullable=True),
                    sa.Column('points', sa.Integer(), nullable=True),
                    sa.Column('match_id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('match_id', 'user_id', name='uix_predictions_match_id_user_id')
                    )
    op.create_index(op.f('ix_predictions_id'), 'predictions', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_predictions_id'), table_name='predictions')
    op.drop_table('predictions')
    op.drop_index(op.f('ix_matches_id'), table_name='matches')
    op.drop_table('matches')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_table('events')
    event_status = postgresql.ENUM('created', 'upcoming', 'ongoing', 'closed', 'completed', 'archived', 'cancelled',
                                   name='eventstatus', create_type=False)
    match_status = postgresql.ENUM('upcoming', 'ongoing', 'completed', name='matchstatus', create_type=False)
    event_status.drop(op.get_bind())
    match_status.drop(op.get_bind())
    # ### end Alembic commands ###
