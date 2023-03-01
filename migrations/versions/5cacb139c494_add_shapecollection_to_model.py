"""Add shapeCollection to Model

Revision ID: 5cacb139c494
Revises: 542bfbdef624
Create Date: 2023-02-28 17:48:33.885131

"""
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import sessionmaker

from buildingmotif.database.tables import DBModel, DBShapeCollection

# revision identifiers, used by Alembic.
revision = "5cacb139c494"
down_revision = "542bfbdef624"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("models", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("shape_collection_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            None, "shape_collection", ["shape_collection_id"], ["id"]
        )

    conn = op.get_bind()
    Session = sessionmaker()

    with Session(bind=conn) as session:
        models = session.query(DBModel).all()

        for m in models:
            shape_collection = DBShapeCollection(graph_id=str(uuid.uuid4()))
            session.add(shape_collection)
            m.shape_collection = shape_collection

        session.commit()

    with op.batch_alter_table("models", schema=None) as batch_op:
        batch_op.alter_column("shape_collection_id", nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("models", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_column("shape_collection_id")

    # ### end Alembic commands ###
