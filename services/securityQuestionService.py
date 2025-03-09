from database import db

from sqlalchemy.orm import Session
from sqlalchemy import select
from circuitbreaker import circuit

from utils.util import decrypted,encrypted,find_user

from models.securityQuestion import SecurityQuestion

def save(user_id,question_data):
  with Session(db.engine) as session:
    with session.begin():
      user = find_user(user_id)
      check_question = session.query(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id).all()
      
      if len(check_question) >= 3:
        raise ValueError(f"{user[0].username} has three questions already. Update a question if you want to add this question.")
      
      if len(check_question) > 0:
        for question in check_question:
          if question.question == question_data['question']:
            raise ValueError("Question already stored")
      
      encripted_answer = encrypted(user[1], question_data['encripted_answer'])
       
          
      new_question = SecurityQuestion(
        user_id = user[0].user_id,
        question = question_data['question'],
        encripted_answer = encripted_answer
      )
      
      session.add(new_question)
      session.commit()
    session.refresh(new_question)
  return new_question

def find(user_id):
  user = find_user(user_id)
  
  security_questions = db.session.query(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id).all()
  
  if security_questions == []:
    return None
  
  for question in security_questions:
    question.encripted_answer = decrypted(user[1], question.encripted_answer)
  
  return security_questions       

def update(user_id,question_data):
  with Session(db.engine) as session:
    with session.begin():
      user = find_user(user_id)
      
      question = session.execute(db.select(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id,
                                                                   SecurityQuestion.question_id == question_data['question_id'])).unique().scalar_one_or_none()
      
      if question is None:
        raise ValueError("Question Not Found")
      
      encrypted_answer = encrypted(user[1],question_data['encripted_answer'])
      
      question.question = question_data['question']
      question.encripted_answer = encrypted_answer
      
      session.commit()
      
    session.refresh(question)
  return question

def delete(user_id,question_data):
  with Session(db.engine) as session:
    with session.begin():
      user = find_user(user_id)
      
      question = session.execute(db.select(SecurityQuestion).where(SecurityQuestion.user_id == user[0].user_id,
                                                                   SecurityQuestion.question_id == question_data['question_id'],
                                                                   SecurityQuestion.question == question_data['question'])).unique().scalar_one_or_none()
      
      if question is None:
        return None
      
      session.delete(question)
      session.commit()
      
  return "successful"

def finder(key,user,rekeyed):
  with Session(db.engine) as session:
    with session.begin():
      questions = session.execute(db.select(SecurityQuestion).where(SecurityQuestion.user_id == user.user_id,)).scalars().all()
      
      if questions != []:
        for question in questions:
          question.encripted_answer = decrypted(key, question.encripted_answer)
          question.encripted_answer = encrypted(rekeyed, question.encripted_answer)
      session.commit()
      
  return questions