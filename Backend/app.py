from datetime import datetime
import os
from flask import Flask, render_template, request, redirect , session, url_for
from gmail_handler import authenticate_gmail, fetch_unread_emails, send_email
from task_manager import TaskManager

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
task_manager = TaskManager('mongodb+srv://test:test123@cluster0.htaswor.mongodb.net/?retryWrites=true&w=majority', 'DB_PFA')



@app.route('/login')
def login():
    GMAIL = authenticate_gmail()
    auth_url = GMAIL.authorization_url()
    return redirect(auth_url)

@app.route('/')
def index():
    if authenticate_gmail():
        if 'user_email' in session:
            user_email = session['user_email']
            tasks = task_manager.view_tasks()
        ###print(tasks)
            return render_template('index.html', user_email=user_email , tasks= tasks)
        else:
            return redirect(url_for('login'))

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        if 'user_email' in session:
            user_email = session['user_email']
            name = request.form.get('name')
            description = request.form.get('description')
            category = request.form.get('category')
            task_date_str = request.form.get('finish_date')  
            task_date = datetime.strptime(task_date_str, '%Y-%m-%d')
            task_manager.add_task(user_email, name, description, category,task_date)
            return redirect('/list_tasks')
    return render_template('add_task.html')


@app.route('/update/<numeric_id>', methods=['GET', 'POST'])
def update_task(numeric_id):
    if request.method == 'GET':
        task = task_manager.get_task_by_numeric_id(int(numeric_id))
        return render_template('update.html', task=task)
    elif request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        completed = request.form.get('completed') == 'on'
        task_manager.update_task(int(numeric_id), name, description, category, completed)
        return redirect('/list_tasks')

@app.route('/delete/<numeric_id>')
def delete_task(numeric_id):
    task_manager.delete_task(int(numeric_id))
    return redirect('/list_tasks')

@app.route('/list_tasks')
def list_tasks():
    tasks = task_manager.view_tasks()
    return render_template('list_tasks.html', tasks=tasks)

@app.route('/logout')
def logout():
    session.clear()
    try:
        os.remove('storage.json')
        print('storage.json deleted successfully.')
    except FileNotFoundError:
        print('storage.json not found.')

    return redirect(url_for('index'))

@app.route('/fetch_emails')
def fetch_emails():
    # Call your Gmail API script
    emails = fetch_unread_emails()
    return render_template('email.html', emails=emails)

@app.route('/compose', methods=['GET', 'POST'])
def compose_email():
    if request.method == 'POST':
        to = request.form.get('to')
        subject = request.form.get('subject')
        body = request.form.get('body')
        
        send_email(to, subject, body)

        return redirect(url_for('compose_email'))  # Redirect to inbox after sending email

    return render_template('compose.html')

if __name__ == '__main__':
    app.run(debug=True)
