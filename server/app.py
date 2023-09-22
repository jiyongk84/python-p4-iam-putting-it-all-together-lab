from flask import request, session
from flask_restful import Resource, Api
from sqlalchemy.exc import IntegrityError

from config import app, db
from models import User, Recipe

api = Api(app)

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get('username')
        password = data['password']
        bio = data.get('bio')
        image_url = data.get('image_url')

        if not username:
            return {"error": "422 Unprocessable Entity"}, 422

        user = User(
            username=username,
            bio=bio,
            image_url=image_url
        )

        user.password_hash = password 

        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id

        
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio,
        }
        
        return user_data, 201
    
class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id is not None:
            user = User.query.get(user_id)
            if user:
                response_data = {
                    'id': user.id, 
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }
                return response_data, 200
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            
            user = User.query.filter_by(username=username).first()
            if user and (password is None or user.authenticate(password)):
                session['user_id'] = user.id
                response_data = {
                    'user_id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }
                return response_data, 200
            else:
                return {'error': 'Unauthorized'}, 401
        except Exception as e:
            return {'error': str(e)}, 500

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return {}, 204
        else:
            return {'error':'unauthorized'}, 401


class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            recipes = Recipe.query.all()
            recipe_data = []
            for recipe in recipes:
                recipe_data.append({
                    'title': recipe.title,
                    'instructions': recipe.instructions,
                    'minutes_to_complete': recipe.minutes_to_complete,
                    'user': {
                        'user_id': recipe.user.id,
                        'username': recipe.user.username,
                        'image_url': recipe.user.image_url,
                        'bio': recipe.user.bio
                    }
                })
            return recipe_data, 200
        return {'error': 'Unauthorized'}, 401

    def post(self):
        user_id = session.get('user_id')
        if user_id:
            try:
                data = request.get_json()
                title = data.get('title')
                instructions = data.get('instructions')
                minutes_to_complete = data.get('minutes_to_complete')
                
                # Create a new recipe
                new_recipe = Recipe(
                    title=title,
                    instructions=instructions,
                    minutes_to_complete=minutes_to_complete,
                    user_id=user_id
                )
                db.session.add(new_recipe)
                db.session.commit()
                
                response_data = {
                    'title': new_recipe.title,
                    'instructions': new_recipe.instructions,
                    'minutes_to_complete': new_recipe.minutes_to_complete,
                    'user': {
                        'user_id': new_recipe.user.id,
                        'username': new_recipe.user.username,
                        'image_url': new_recipe.user.image_url,
                        'bio': new_recipe.user.bio
                    }
                }
                return response_data, 201
            except IntegrityError:
                db.session.rollback()
                return {'error': 'Recipe data is invalid'}, 422
            except Exception as e:
                return {'error': str(e)}, 500
        return {'error': 'Unauthorized'}, 401

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
