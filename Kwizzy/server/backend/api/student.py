from flask_restful import Resource
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from ..utils import role_required
from ..models import User, QuizResult, Quiz, Chapter, Subject
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from .. import db


class Student(Resource):
    def to_dict(self, user):
        """Convert user object to dictionary with relevant student information"""
        # Calculate quiz statistics
        total_quizzes = len(user.quiz_results)
        completed_quizzes = [
            result for result in user.quiz_results if result.marks_scored is not None
        ]
        latest_activity = max([r.completed_at for r in user.quiz_results], default=None)

        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "dob": user.dob.strftime("%Y-%m-%d") if user.dob else None,
            "qualification": user.qualification,
            "profile_pic": user.profile_pic,
            "quiz_stats": {
                "total_quizzes_attempted": total_quizzes,
                "quizzes_completed": len(completed_quizzes),
                "average_score": self.calculate_average_score(user.quiz_results),
                "total_score": sum(r.marks_scored or 0 for r in user.quiz_results),
                "last_active": (
                    latest_activity.strftime("%Y-%m-%d %H:%M:%S")
                    if latest_activity
                    else None
                ),
                "performance_percentage": self.calculate_performance_percentage(
                    user.quiz_results
                ),
            },
        }

    def get_recent_activity(self, student_id):
        """Get student's recent activity"""
        try:
            recent_results = (
                QuizResult.query.filter_by(user_id=student_id)
                .order_by(QuizResult.completed_at.desc())
                .limit(5)
                .all()
            )

            return [
                {
                    "quiz_name": result.quiz.name,
                    "marks_scored": result.marks_scored,
                    "total_marks": result.total_marks,
                    "percentage": (
                        round((result.marks_scored / result.total_marks * 100), 2)
                        if result.total_marks
                        else 0
                    ),
                    "completed_at": result.completed_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for result in recent_results
            ]
        except Exception as e:
            return {"error": str(e)}

    def get_subject_performance(self, student_id):
        """Get subject-wise performance breakdown"""
        try:
            results = (
                db.session.query(
                    Subject.name,
                    func.avg(
                        (QuizResult.marks_scored * 100.0) / QuizResult.total_marks
                    ).label("average_score"),
                    func.count(QuizResult.id).label("total_quizzes"),
                )
                .join(Quiz, Quiz.id == QuizResult.quiz_id)
                .join(Chapter, Chapter.id == Quiz.chapter_id)
                .join(Subject, Subject.id == Chapter.subject_id)
                .filter(
                    QuizResult.user_id == student_id,
                    QuizResult.marks_scored.isnot(None),
                )
                .group_by(Subject.name)
                .all()
            )

            return [
                {
                    "subject": row[0],
                    "average_score": round(float(row[1]), 2) if row[1] else 0,
                    "total_quizzes": row[2],
                }
                for row in results
            ]
        except Exception as e:
            return {"error": str(e)}

    def calculate_average_score(self, quiz_results):
        """Calculate average score of all completed quizzes"""
        try:
            completed_results = [r for r in quiz_results if r.marks_scored is not None]
            if not completed_results:
                return 0

            valid_results = [
                (result.marks_scored / result.total_marks) * 100
                for result in completed_results
                if result.total_marks > 0 and result.marks_scored is not None
            ]

            return (
                round(sum(valid_results) / len(valid_results), 2)
                if valid_results
                else 0
            )
        except ZeroDivisionError:
            return 0

    def calculate_performance_percentage(self, quiz_results):
        """Calculate overall performance percentage"""
        total_marks_scored = sum(r.marks_scored or 0 for r in quiz_results)
        total_possible_marks = sum(r.total_marks or 0 for r in quiz_results)

        if total_possible_marks == 0:
            return 0

        return round((total_marks_scored / total_possible_marks) * 100, 2)

    def get_detailed_performance(self, user):
        """Get detailed performance breakdown"""
        quiz_details = []
        for result in user.quiz_results:
            if result.marks_scored is not None:  # Only include completed quizzes
                percentage = (
                    (result.marks_scored / result.total_marks * 100)
                    if result.total_marks > 0
                    else 0
                )
                quiz_details.append(
                    {
                        "quiz_id": result.quiz_id,
                        "quiz_name": result.quiz.name,
                        "marks_scored": result.marks_scored,
                        "total_marks": result.total_marks,
                        "percentage": round(percentage, 2),
                        "completed_at": result.completed_at.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "answers_breakdown": {
                            "total_questions": len(result.user_answers),
                            "correct_answers": len(
                                [a for a in result.user_answers if a.is_correct]
                            ),
                            "incorrect_answers": len(
                                [a for a in result.user_answers if not a.is_correct]
                            ),
                        },
                    }
                )

        return quiz_details

    def get_student_statistics(self):
        """Get overall student statistics"""
        try:
            total_students = User.query.filter_by(role="student").count()
            active_students = (
                User.query.join(QuizResult)
                .filter(
                    User.role == "student",
                    QuizResult.completed_at >= (datetime.now() - timedelta(days=30)),
                )
                .distinct()
                .count()
            )

            # Get qualification distribution
            qualification_stats = (
                db.session.query(User.qualification, func.count(User.id))
                .filter_by(role="student")
                .group_by(User.qualification)
                .all()
            )

            # Get performance distribution
            performance_ranges = {
                "excellent": (90, 100),
                "good": (70, 89),
                "average": (50, 69),
                "below_average": (0, 49),
            }

            performance_stats = {}
            for range_name, (min_score, max_score) in performance_ranges.items():
                count = (
                    User.query.join(QuizResult)
                    .filter(
                        User.role == "student",
                        QuizResult.marks_scored
                        * 100
                        / QuizResult.total_marks.between(min_score, max_score),
                    )
                    .distinct()
                    .count()
                )
                performance_stats[range_name] = count

            return {
                "total_students": total_students,
                "active_students": active_students,
                "inactive_students": total_students - active_students,
                "qualification_distribution": dict(qualification_stats),
                "performance_distribution": performance_stats,
            }
        except Exception as e:
            return {"error": str(e)}, 500

    @jwt_required()
    @role_required("admin")
    def get(self, student_id=None):
        try:
            if not self.validate_pagination_params(
                request.args.get("page", 1), request.args.get("per_page", 10)
            ):
                return self.format_response(None, 400, "Invalid pagination parameters")
            if student_id:
                student = User.query.filter_by(id=student_id, role="student").first()
                if not student:
                    return {"message": "Student not found"}, 404

                return {
                    "student_info": self.to_dict(student),
                    "detailed_performance": self.get_detailed_performance(student),
                }, 200

            # Get all students with pagination and filters
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            search = request.args.get("search", "").strip()
            sort_by = request.args.get("sort_by", "name")
            order = request.args.get("order", "asc")

            query = User.query.filter_by(role="student")

            if search:
                query = query.filter(
                    (User.name.ilike(f"%{search}%"))
                    | (User.email.ilike(f"%{search}%"))
                    | (User.qualification.ilike(f"%{search}%"))
                )

            # Apply sorting
            if sort_by == "performance":
                # Complex sorting by average performance
                if order == "desc":
                    query = query.order_by(
                        desc(
                            func.coalesce(
                                func.avg(
                                    (QuizResult.marks_scored * 100.0)
                                    / QuizResult.total_marks
                                ),
                                0,
                            )
                        )
                    )
                else:
                    query = query.order_by(
                        func.coalesce(
                            func.avg(
                                (QuizResult.marks_scored * 100.0)
                                / QuizResult.total_marks
                            ),
                            0,
                        )
                    )
            else:
                if order == "desc":
                    query = query.order_by(desc(getattr(User, sort_by)))
                else:
                    query = query.order_by(getattr(User, sort_by))

            pagination = query.paginate(page=page, per_page=per_page)

            return self.format_response(
                {
                    "students": [self.to_dict(student) for student in pagination.items],
                    "total": pagination.total,
                    "pages": pagination.pages,
                    "current_page": page,
                    "per_page": per_page,
                }
            )

        except Exception as e:
            return self.format_response(None, 500, f"Error fetching students: {str(e)}")

    @jwt_required()
    @role_required("admin")
    def get_statistics(self):
        """Get overall student statistics"""
        return self.get_student_statistics(), 200

    @jwt_required()
    @role_required("admin")
    def get_student_activity(self, student_id):
        """Get student's recent activity"""
        return self.get_recent_activity(student_id), 200

    @jwt_required()
    @role_required("admin")
    def get_student_subjects(self, student_id):
        """Get student's subject-wise performance"""
        return self.get_subject_performance(student_id), 200

    def validate_pagination_params(self, page, per_page):
        """Validate pagination parameters"""
        try:
            page = int(page)
            per_page = int(per_page)
            if page < 1 or per_page < 1:
                raise ValueError
        except ValueError:
            return False
        return True

    def format_response(self, data, status_code=200, message=None):
        """Format API response"""
        response = {"status": "success" if status_code < 400 else "error", "data": data}
        if message:
            response["message"] = message
        return response, status_code


class StudentStatistics(Resource):
    @jwt_required()
    @role_required("admin")
    def get(self):
        return Student().get_student_statistics(), 200


class StudentActivity(Resource):
    @jwt_required()
    @role_required("admin")
    def get(self, student_id):
        return Student().get_recent_activity(student_id), 200


class StudentSubjectPerformance(Resource):
    @jwt_required()
    @role_required("admin")
    def get(self, student_id):
        return Student().get_subject_performance(student_id), 200
