from flask import Flask, redirect, render_template, request, jsonify, abort
from flasgger import Swagger
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
import sys
from waitress import serve

app = Flask(__name__)

app.config['SWAGGER'] = {
    'swagger': '2.0',
    'info': {
        'title': 'Todo API',
        'description': 'A simple Todo API',
        'version': '1.0.0'
    },
    'basepath': '/api'
}

swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/"
}

swagger = Swagger(app, config=swagger_config)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite'
db = SQLAlchemy(app)

class Todo(db.Model, SerializerMixin):
    task_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return '<Task %r>' % self.task_id


@app.route("/swagger")
def spec():
    return swagger

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template("index.html", tasks=tasks)
    task_content = request.form['content']
    new_task = Todo(content=task_content)

    try:
        db.session.add(new_task)
        db.session.commit()
        return redirect('/')
    except Exception:
        return 'There was an issue adding your task.'

@app.route('/delete/<int:task_id>')
def delete(task_id):
    
    task_to_delete = Todo.query.get_or_404(task_id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except Exception:
        return 'There was an issue deleting your task.'

@app.route('/update/<int:task_id>', methods=['GET', 'POST'])
def update(task_id):
    
    task_to_update = Todo.query.get_or_404(task_id)
    if request.method == 'GET':
        return render_template('update.html', task=task_to_update)
    task_to_update.content = request.form['content']
    try:
        db.session.commit()
        return redirect('/')
    except Exception:
        return 'There was an issue updating your task.'

@app.route('/api/get', methods=['GET'])
def api_get():
    """
    Get a list with tasks objects
    ---
    tags:
      - Get Tasks
    definitions:
        Task:
          type: object
          properties:
            content:
              type: string
            date_created:
              type: string
            task_id:
              type: integer 
    responses:
        200:
            description: A list of all tasks
            schema:
              id: Task
              type: object
              properies:
                  tasks:
                    type: array
                    items:
                      $ref: '#/definitions/Task'
    """
    tasks_raw = Todo.query.order_by(Todo.date_created).all()
    tasks = [task.to_dict() for task in tasks_raw]
    return jsonify(tasks)

@app.route('/api/add', methods=['POST'])
def api_add():
    """
    Add a task
    ---
    tags:
      - Add Task
    parameters:
        - in: body
          name: body
          schema:
            properties:
              task_description:
                description: The new task description
                required: true
                type: string
                default: New task description
    responses:
        204:
            description: The task was added
        404:
            description: The task was not found
    """
    if not request.get_json():
        app.logger.debug('Problems with json')
        abort(400)
    
    data = request.get_json(force=True)

    if not data.get('task_description') and isinstance(data.get('task_description'), str):
        app.logger.debug('No task description provided')
        return jsonify({'message': 'No task description found'}), 400

    task_description = data.get('task_description')

    new_task = Todo(content=task_description)

    try:
        db.session.add(new_task)
        db.session.commit()
        return jsonify({}), 204
    except Exception:
        return 'There was an issue adding your task.'

@app.route('/api/update', methods=['POST'])
def api_update():
    """
    Update a task
    ---
    tags:
      - Update Task
    parameters:
        - in: body
          name: body
          schema:
            properties:
              task_id:
                description: The ID of the task to update
                required: true
                type: integer
                default: 1
              task_description:
                description: The new task description
                required: true
                type: string
                default: New task description
    responses:
        204:
            description: The task was updated
        404:
            description: The task was not found
    """
    if not request.get_json():
        app.logger.debug('Problems with json')
        abort(400)
    
    data = request.get_json(force=True)

    if not data.get('task_id') and isinstance(data.get('task_id'), int):
        app.logger.debug('No task id provided')
        return jsonify({'message': 'No task id found'}), 400

    task_id = data.get('task_id')

    task_to_update = Todo.query.get_or_404(task_id)

    if not data.get('task_description') and isinstance(data.get('task_description'), str):
        app.logger.debug('No task description provided')
        return jsonify({'message': 'No task description found'}), 400

    task_to_update.content = data.get('task_description')

    try:
        db.session.commit()
        return jsonify({}), 204
    except Exception:
        return 'There was an issue updating your task.'

@app.route('/api/delete/<int:task_id>', methods=['DELETE'])
def api_delete(task_id):
    """
    Delete a task
    ---
    tags:
      - Delete Task
    parameters:
        - name: task_id
          in: path
          description: The ID of the task to delete
          required: true
          type: integer
    responses:
        200:
            description: The task was deleted
        404:
            description: The task was not found
    """

    task_to_delete = Todo.query.get_or_404(task_id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return jsonify({})
    except Exception:
        return 'There was an issue deleting your task.'

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'dev':
            app.run(debug=True)
        elif sys.argv[1] == 'prod':
            serve(app, host='0.0.0.0', port=8080, url_scheme = 'https')
    app.run(debug=True)
