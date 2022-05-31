from flask import Flask, redirect, render_template, request, jsonify, abort
from flask_swagger import swagger
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite'
db = SQLAlchemy(app)

class Todo(db.Model, SerializerMixin):
    task_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return '<Task %r>' % self.task_id


@app.route("/spec")
def spec():
    swag = swagger(app)
    swag['swagger'] = '2.0'
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "Todo API"

    return jsonify(swag)

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
    """
    Delete a task
    ---
    tags:
      - delete
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
        return redirect('/')
    except Exception:
        return 'There was an issue deleting your task.'

@app.route('/update/<int:task_id>', methods=['GET', 'POST'])
def update(task_id):
    """
    Update a task
    ---
    tags:
      - update
    parameters:
        - name: task_id
          in: path
          description: The ID of the task to update
          required: true
          type: integer
    responses:
        200:
            description: The task was updated
        404:
            description: The task was not found
    """
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
    """Get all tasks
    @return: 200: an array of all tasks
    """
    tasks_raw = Todo.query.order_by(Todo.date_created).all()
    tasks = [task.to_dict() for task in tasks_raw]
    return jsonify(tasks)

@app.route('/api/add', methods=['POST'])
def api_add():
    """Add a new task
    @param task_description: post : Data for task description
    @return: 200: New task added
    @raise 400: Bad request
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
        return jsonify({}, 200)
    except Exception:
        return 'There was an issue adding your task.'

@app.route('/api/update', methods=['POST'])
def api_update():
    """Update a task
    @param task_id: post : The ID of the task to update
    @param task_description: post : Data for task description
    @return: 200: Task updated
    @raise 400: Bad request
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
        return jsonify({}, 200)
    except Exception:
        return 'There was an issue updating your task.'

@app.route('/api/delete/<int:task_id>', methods=['DELETE'])
def api_delete(task_id):
    """Delete a task
    @param task_id: post : The ID of the task to delete
    @return: 200: Task deleted
    @raise 400: Bad request
    """

    task_to_delete = Todo.query.get_or_404(task_id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return jsonify({}, 200)
    except Exception:
        return 'There was an issue deleting your task.'

if __name__ == "__main__":
    app.run(debug=True)