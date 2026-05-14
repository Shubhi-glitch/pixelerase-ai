from datetime import datetime

from app import db


class ImageHistory(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    image_url = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):

        return f'<Image {self.id}>'