from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.sqlite'
db = SQLAlchemy(app)

class Todo(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return '<Task %r>' % self.task_id

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method != 'POST':
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
    if request.method != 'POST':
        return render_template('update.html', task=task_to_update)
    task_to_update.content = request.form['content']
    try:
        db.session.commit()
        return redirect('/')
    except Exception:
        return 'There was an issue updating your task.'

    

if __name__ == "__main__":
    app.run(debug=True)