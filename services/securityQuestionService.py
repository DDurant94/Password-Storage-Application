from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select

from utils.utils import find_user
from utils.encryption_utils import decrypted, encrypted, rekey_collection
from utils.circuitbreaker import CircuitBreaker
from caching import (
  DEFAULT_CACHE_TIMEOUT,
  SHORT_CACHE_TIMEOUT,
  cached_result,
  build_cache_key,
  invalidate_cache,
)

from models.securityQuestion import SecurityQuestion


class SecurityQuestionService:
  """Encapsulates security-question business logic with injectable collaborators."""

  def __init__(self, session_factory=None):
    self._session_factory = session_factory

  def save(self, user_id, question_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)
        check_question = session.query(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id).all()

        if len(check_question) >= 3:
          raise ValueError(f"{user[0].username} has three questions already. Update a question if you want to add this question.")

        if len(check_question) > 0:
          for question in check_question:
            if question.question == question_data['question']:
              raise ValueError("Question already stored")

        encrypted_answer = encrypted(user[1], question_data['encripted_answer'])

        new_question = SecurityQuestion(
          user_id=user[0].user_id,
          question=question_data['question'],
          encripted_answer=encrypted_answer
        )

        session.add(new_question)
      session.refresh(new_question)
    invalidate_cache()
    return new_question

  def find(self, user_id):
    user = find_user(user_id)
    cache_key = build_cache_key('security_question', 'list', user[0].user_id)

    return cached_result(cache_key, lambda: self._load_security_questions(user), timeout=SHORT_CACHE_TIMEOUT)

  def _load_security_questions(self, user):
    security_questions = db.session.query(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id).all()

    if security_questions == []:
      return None

    for question in security_questions:
      question.encripted_answer = decrypted(user[1], question.encripted_answer)

    return security_questions

  def update(self, user_id, question_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)

        question = session.execute(db.select(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id,
                                                                     SecurityQuestion.question_id == question_data['question_id'])).unique().scalar_one_or_none()

        if question is None:
          raise ValueError("Question Not Found")

        encrypted_answer = encrypted(user[1], question_data['encripted_answer'])

        question.question = question_data['question']
        question.encripted_answer = encrypted_answer

      session.refresh(question)
    invalidate_cache()
    return question

  def delete(self, user_id, question_data):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        user = find_user(user_id)

        question = session.execute(db.select(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id,
                                                                     SecurityQuestion.question_id == question_data['question_id'],
                                                                     SecurityQuestion.question == question_data['question'])).unique().scalar_one_or_none()

        if question is None:
          return None

        session.delete(question)

    invalidate_cache()
    return "successful"

  def finder(self, key, user, rekeyed):
    session_factory = self._session_factory or Session
    with session_factory(db.engine) as session:
      with session.begin():
        questions = session.execute(db.select(SecurityQuestion).where(SecurityQuestion.user_id == user.user_id)).scalars().all()
        rekey_collection(questions, key, rekeyed, 'encripted_answer')

    return questions


security_question_service = SecurityQuestionService()
service_breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=10)


@service_breaker
def save(user_id, question_data):
  return security_question_service.save(user_id, question_data)


@service_breaker
def find(user_id):
  return security_question_service.find(user_id)


@service_breaker
def update(user_id, question_data):
  return security_question_service.update(user_id, question_data)


@service_breaker
def delete(user_id, question_data):
  return security_question_service.delete(user_id, question_data)


@service_breaker
def finder(key, user, rekeyed):
  return security_question_service.finder(key, user, rekeyed)