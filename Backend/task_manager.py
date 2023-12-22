# task_manager.py

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta

class TaskManager:
    def __init__(self, connection_uri, database_name):
        # Connect to MongoDB
        self.client = MongoClient(connection_uri)
        self.db = self.client[database_name]
        self.tasks_collection = self.db["tasks"]

        # Check if the MongoDB connection is successful
        try:
            self.client.admin.command('ping')
            print("-------------------------------------Successfully connected to MongoDB!")
        except Exception as e:
            print(f"-------------------------------------Failed to connect to MongoDB. Error: {e}")

    def add_task(self, user_email, name, description, category, finish_date,completed=False):
        # Find the maximum numeric_id in the collection and increment by 1
        max_numeric_id = self.tasks_collection.find_one(sort=[("numeric_id", -1)])
        next_numeric_id = (max_numeric_id["numeric_id"] + 1) if max_numeric_id else 0

        task = {
            'numeric_id': next_numeric_id,
            'user_email': user_email, 
            'name': name,
            'description': description,
            'category': category,
            'finish_date': finish_date,
            'completed': completed
        }

        result = self.tasks_collection.insert_one(task)
        print(f'Task "{name}" added successfully with numeric ID: {next_numeric_id} for user: {user_email}')
        return f'Task "{name}" added successfully with numeric ID: {next_numeric_id} for user: {user_email}'

    def view_tasks(self):
        tasks_cursor = self.tasks_collection.find()
        tasks = list(tasks_cursor)  # Convert the cursor to a list of dictionaries
        task_count = len(tasks)

        if task_count == 0:
            print("No tasks available.")
            return []
        else:
            print(f'Total tasks: {task_count}')
            for task in tasks:
                print(f'Task ID: {task["numeric_id"]}')
                #print(f'User Email: {task["user_email"]}')  # Include user_email in the output
                print(f'Task Name: {task["name"]}')
                print(f'Task Description: {task["description"]}')
                print(f'Task Category: {task["category"]}')
                print(f'Task Completed: {task["completed"]}')
                print('---------------------')

            return tasks


    def get_task_by_numeric_id(self, numeric_id):
        return self.tasks_collection.find_one({'numeric_id': numeric_id})

    def update_task(self, numeric_id, name, description, category, completed):
        task = {
            'name': name,
            'description': description,
            'category': category,
            'completed': completed
        }
        result = self.tasks_collection.update_one({'numeric_id': numeric_id}, {'$set': task})
        if result.modified_count > 0:
            print(f'Task with numeric ID {numeric_id} updated successfully.')
            return f'Task updated successfully.'
        else:
            print(f'Invalid numeric ID {numeric_id} or no modifications made.')
            return 'Invalid numeric ID or no modifications made.'

    def delete_task(self, numeric_id):
        result = self.tasks_collection.delete_one({'numeric_id': numeric_id})
        if result.deleted_count > 0:
            print(f'Task with numeric ID {numeric_id} deleted successfully.')
            return f'Task deleted successfully.'
        else:
            print(f'Invalid numeric ID {numeric_id} or task not found.')
            return 'Invalid numeric ID or task not found.'
