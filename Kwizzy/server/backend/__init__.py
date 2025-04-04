from flask import Flask
from werkzeug.utils import safe_join
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_migrate import Migrate
import os
from os import path
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache
from dotenv import load_dotenv
from celery import Celery
from celery.schedules import crontab


load_dotenv()


db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
cache = Cache()

celery = Celery(
    "backend",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config.from_object("backend.config.Config")
    app.config["ALLOWED_EXTENSIONS"] = set(
        os.getenv("ALLOWED_EXTENSIONS", "").split(",")
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Configure Celery
    celery.conf.update(
        enable_utc=False,
        timezone="Asia/Kolkata",
        broker_connection_retry_on_startup=True,
        task_track_started=True,
        task_ignore_result=False,
        beat_schedule={
            "daily-reminder": {
                "task": "backend.tasks.celery_tasks.send_daily_reminders",
                "schedule": crontab(
                    hour=22,
                    minute=57,
                ),
            },
            "monthly-report": {
                "task": "backend.tasks.celery_tasks.generate_monthly_activity_report",
                "schedule": crontab(hour=22, minute=57, day_of_month="4"),
            },
            "cleanup-old-exports": {
                "task": "backend.api.csv.cleanup_old_exports",
                "schedule": crontab(minute=0, hour=0),
            },
        },
    )

    cache.init_app(
        app,
        config={
            "CACHE_TYPE": os.getenv("CACHE_TYPE", "redis"),
            "CACHE_REDIS_URL": os.getenv("CACHE_REDIS_URL"),
            "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300)),
        },
    )
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")
    api = Api(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5173"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Range"],
                "supports_credentials": True,
            }
        },
    )

    @app.after_request
    def apply_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    from .api.auth import Login, Register, ForgotPasswordAPI, ResetPasswordAPI
    from .api.student import (
        Student,
        StudentActivity,
        StudentSubjectPerformance,
    )
    from .api.user import UserApi
    from .api.subject import SubjectApi
    from .api.chapter import ChapterApi
    from .api.quiz import QuizApi
    from .api.question import QuestionApi
    from .api.options import OptionApi
    from .api.options import OptionsBulkApi
    from .api.serve_file import FileApi
    from .api.user_answer import UserAnswerApi
    from .api.quiz_result import QuizResultApi
    from .api.chart_api import ChartDataApi
    from .api.student_charts import StudentChartsApi
    from .api.taskAPI import TaskAPI
    from .api.csv import UserQuizExportAPI, AdminQuizExportAPI
    from .api.payment import PaymentApi, TransactionHistoryAPI, TransactionExportAPI

    api.add_resource(Student, "/api/students", "/api/student/<int:student_id>")
    api.add_resource(StudentActivity, "/api/student/<int:student_id>/activity")
    api.add_resource(
        StudentSubjectPerformance, "/api/student/<int:student_id>/subjects"
    )
    api.add_resource(Login, "/api/login")
    api.add_resource(Register, "/api/register")
    api.add_resource(ForgotPasswordAPI, "/api/auth/forgot-password")
    api.add_resource(ResetPasswordAPI, "/api/auth/reset-password")
    api.add_resource(UserApi, "/api/user", "/api/user/<int:user_id>")
    api.add_resource(SubjectApi, "/api/subject", "/api/subject/<int:subject_id>")
    api.add_resource(ChapterApi, "/api/chapter", "/api/chapter/<int:chapter_id>")
    api.add_resource(
        QuizApi,
        "/api/quizzes",
        "/api/quizzes/chapter/<int:chapter_id>",
        "/api/quizzes/<int:quiz_id>",
    )
    api.add_resource(
        QuestionApi,
        "/api/quizzes/<int:quiz_id>/questions",
        "/api/quizzes/<int:quiz_id>/questions/<int:question_id>",
    )
    api.add_resource(
        OptionApi,
        "/api/questions/<int:question_id>/options",
        "/api/options/<int:option_id>",
    )
    api.add_resource(OptionsBulkApi, "/api/questions/<int:question_id>/options/bulk")
    api.add_resource(FileApi, "/api/uploads/subjects/<path:filename>")
    api.add_resource(
        QuizResultApi, "/api/quiz-results", "/api/quiz-results/<int:result_id>"
    )
    api.add_resource(
        UserAnswerApi, "/api/user-answers", "/api/user-answers/<int:answer_id>"
    )
    api.add_resource(
        ChartDataApi, "/api/admin/charts", "/api/charts/<string:chart_type>"
    )
    api.add_resource(StudentChartsApi, "/api/student/charts")
    api.add_resource(TaskAPI, "/api/tasks", "/api/tasks/<int:task_id>")
    api.add_resource(UserQuizExportAPI, "/api/export/user-csv")
    api.add_resource(AdminQuizExportAPI, "/api/export/admin-csv")
    api.add_resource(
        PaymentApi,
        "/api/payments",
        "/api/payments/status/<int:user_id>/<int:quiz_id>",
    )
    api.add_resource(
        TransactionHistoryAPI,
        "/api/payments/history",
        "/api/payments/history/<int:user_id>",
    )
    api.add_resource(
        TransactionExportAPI,
        "/api/export/transactions",
        "/api/export/transactions/<int:student_id>",
    )

    with app.app_context():
        db.create_all()
    return app


app = create_app()


def create_database(app):
    if not path.exists("server/" + DB_NAME):
        db.create_all(app=app)
        print("Created Database!")
