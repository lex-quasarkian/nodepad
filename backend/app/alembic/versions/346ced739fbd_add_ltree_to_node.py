"""add_ltree_to_node

Revision ID: 346ced739fbd
Revises: fe56fa70289e
Create Date: 2026-04-29 13:18:09.165057

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '346ced739fbd'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    # Enable ltree extension
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree")

    # Add columns as nullable first
    op.add_column('node', sa.Column('path', sqlalchemy_utils.types.ltree.LtreeType(), nullable=True))
    op.add_column('node', sa.Column('level', sa.Integer(), server_default='0', nullable=False))
    
    # Populate path and level for existing nodes
    op.execute("""
        WITH RECURSIVE node_paths AS (
            SELECT id, CAST(REPLACE(CAST(id AS TEXT), '-', '') AS ltree) AS path, 0 AS level
            FROM node
            WHERE parent_id IS NULL
            UNION ALL
            SELECT n.id, np.path || CAST(REPLACE(CAST(n.id AS TEXT), '-', '') AS ltree), np.level + 1
            FROM node n
            JOIN node_paths np ON n.parent_id = np.id
        )
        UPDATE node
        SET path = node_paths.path, level = node_paths.level
        FROM node_paths
        WHERE node.id = node_paths.id
    """)
    
    # Set path as non-nullable
    op.alter_column('node', 'path', nullable=False)

    op.alter_column('node', 'content',
               existing_type=sa.TEXT(),
               type_=sa.String(),
               existing_nullable=False)
    
    # Handle index changes
    # op.drop_index(op.f('idx_node_list_parent_pos'), table_name='node') 
    # Wait, let's check if the index exists with that name. 
    # In the previous turn it said "Detected removed index 'idx_node_list_parent_pos'"
    # But in the model it was 'idx_nodes_list_parent_pos'. 
    # I'll just follow what autogenerate suggested for indexes.
    
    try:
        op.drop_index('idx_node_list_parent_pos', table_name='node')
    except:
        pass
        
    op.create_index('idx_node_level', 'node', ['level'], unique=False)
    op.create_index('idx_node_path_gist', 'node', ['path'], unique=False, postgresql_using='gist')
    op.create_index('idx_nodes_list_parent_pos', 'node', ['nodelist_id', 'parent_id', 'position'], unique=False)


def downgrade():
    op.drop_index('idx_nodes_list_parent_pos', table_name='node')
    op.drop_index('idx_node_path_gist', table_name='node', postgresql_using='gist')
    op.drop_index('idx_node_level', table_name='node')
    op.create_index('idx_node_list_parent_pos', 'node', ['nodelist_id', 'parent_id', 'position'], unique=False)
    op.alter_column('node', 'content',
               existing_type=sa.String(),
               type_=sa.TEXT(),
               existing_nullable=False)
    op.drop_column('node', 'level')
    op.drop_column('node', 'path')
    # We don't drop the extension as it might be used elsewhere
