import os
from datetime import datetime

import boto3
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


app = Flask(__name__)


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "classroomdb")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")


if all([DB_HOST, DB_USER, DB_PASSWORD]):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

s3 = boto3.client("s3", region_name=AWS_REGION)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date_of_entry = db.Column(db.Date, nullable=False)
    course = db.Column(db.String(120), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)
    subscription_end = db.Column(db.Date, nullable=False)
    document_key = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date_of_entry": self.date_of_entry.isoformat(),
            "course": self.course,
            "payment_status": self.payment_status,
            "subscription_end": self.subscription_end.isoformat(),
            "document_key": self.document_key,
        }


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/students", methods=["GET"])
def get_students():
    students = Student.query.order_by(Student.id.desc()).all()

    return jsonify([student.to_dict() for student in students])


@app.route("/api/students", methods=["POST"])
def create_student():

    name = request.form.get("name")
    date_of_entry = request.form.get("date_of_entry")
    course = request.form.get("course")
    payment_status = request.form.get("payment_status")
    subscription_end = request.form.get("subscription_end")

    if not all([
        name,
        date_of_entry,
        course,
        payment_status,
        subscription_end,
    ]):
        return jsonify({"error": "All fields are required"}), 400

    document_key = None

    uploaded_file = request.files.get("document")

    if uploaded_file and uploaded_file.filename and S3_BUCKET:

        filename = secure_filename(uploaded_file.filename)

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        document_key = f"student-documents/{timestamp}-{filename}"

        s3.upload_fileobj(
            uploaded_file,
            S3_BUCKET,
            document_key
        )

    student = Student(
        name=name,
        date_of_entry=datetime.strptime(
            date_of_entry,
            "%Y-%m-%d"
        ).date(),
        course=course,
        payment_status=payment_status,
        subscription_end=datetime.strptime(
            subscription_end,
            "%Y-%m-%d"
        ).date(),
        document_key=document_key
    )

    db.session.add(student)
    db.session.commit()

    return jsonify(student.to_dict()), 201


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):

    student = Student.query.get_or_404(student_id)

    data = request.get_json()

    if "name" in data:
        student.name = data["name"]

    if "course" in data:
        student.course = data["course"]

    if "payment_status" in data:
        student.payment_status = data["payment_status"]

    if "date_of_entry" in data:
        student.date_of_entry = datetime.strptime(
            data["date_of_entry"],
            "%Y-%m-%d"
        ).date()

    if "subscription_end" in data:
        student.subscription_end = datetime.strptime(
            data["subscription_end"],
            "%Y-%m-%d"
        ).date()

    db.session.commit()

    return jsonify(student.to_dict())


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):

    student = Student.query.get_or_404(student_id)

    if student.document_key and S3_BUCKET:
        try:
            s3.delete_object(
                Bucket=S3_BUCKET,
                Key=student.document_key
            )
        except Exception:
            pass

    db.session.delete(student)
    db.session.commit()

    return jsonify({
        "message": "Student deleted successfully"
    })


@app.route(
    "/api/students/<int:student_id>/document",
    methods=["GET"]
)
def student_document(student_id):

    student = Student.query.get_or_404(student_id)

    if not student.document_key:
        return jsonify({
            "error": "No document uploaded"
        }), 404

    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET,
            "Key": student.document_key
        },
        ExpiresIn=300
    )

    return jsonify({"url": url})


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
