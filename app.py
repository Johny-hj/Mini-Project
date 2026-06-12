import os

from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

# Course Table
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    progress = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="Not Started")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class TaskProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    task_id = db.Column(db.String(120), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', 'task_id', name='unique_user_course_task'),
    )

CURRICULUM = {
    'dsa': {
        'title': 'DSA',
        'description': 'Data structures and algorithms from absolute basics to interview-ready problem solving.',
        'concepts': [
            {
                'title': 'Programming logic and complexity',
                'tasks': [
                    'Understand input, output, variables, loops, and conditions',
                    'Learn time complexity using O(1), O(n), O(n log n), and O(n^2)',
                    'Solve 5 dry-run problems by tracing each step on paper',
                ],
            },
            {
                'title': 'Arrays and strings',
                'tasks': [
                    'Practice indexing, traversal, insertion, deletion, and searching',
                    'Solve basic two-pointer problems on arrays',
                    'Solve string reversal, palindrome, frequency count, and anagram tasks',
                ],
            },
            {
                'title': 'Recursion and backtracking',
                'tasks': [
                    'Understand base case, recursive case, and call stack',
                    'Write factorial, Fibonacci, sum of array, and power recursively',
                    'Solve subset generation and simple permutation problems',
                ],
            },
            {
                'title': 'Linked lists, stacks, and queues',
                'tasks': [
                    'Implement singly linked list insert, delete, and search',
                    'Use stacks for balanced brackets and undo-style problems',
                    'Use queues for simple scheduling and BFS-style traversal',
                ],
            },
            {
                'title': 'Trees, graphs, sorting, and searching',
                'tasks': [
                    'Learn binary tree traversal: inorder, preorder, postorder, level order',
                    'Practice binary search, bubble sort, selection sort, merge sort, and quick sort',
                    'Understand graph basics with BFS and DFS on an adjacency list',
                ],
            },
        ],
    },
    'python': {
        'title': 'Python',
        'description': 'A complete beginner path from syntax to files, functions, OOP, and mini projects.',
        'concepts': [
            {
                'title': 'Python basics',
                'tasks': [
                    'Install Python and run code from terminal and an editor',
                    'Learn variables, data types, input, output, and type conversion',
                    'Build a simple calculator using arithmetic operators',
                ],
            },
            {
                'title': 'Control flow',
                'tasks': [
                    'Use if, elif, and else for decision making',
                    'Practice for loops and while loops',
                    'Build a number guessing game',
                ],
            },
            {
                'title': 'Collections',
                'tasks': [
                    'Learn lists, tuples, sets, and dictionaries',
                    'Practice list methods, dictionary lookup, and frequency counting',
                    'Build a contact book using dictionaries',
                ],
            },
            {
                'title': 'Functions and modules',
                'tasks': [
                    'Write reusable functions with parameters and return values',
                    'Understand scope, default arguments, and imports',
                    'Create a small utility module and import it in another file',
                ],
            },
            {
                'title': 'Files, errors, and OOP',
                'tasks': [
                    'Read from and write to text files',
                    'Handle errors with try and except',
                    'Create a class with attributes, methods, and objects',
                ],
            },
        ],
    },
    'sql': {
        'title': 'SQL',
        'description': 'Query data confidently with filtering, joins, grouping, and table design basics.',
        'concepts': [
            {
                'title': 'Database and table basics',
                'tasks': [
                    'Understand rows, columns, tables, primary keys, and data types',
                    'Create a simple students table',
                    'Insert, update, and delete sample records',
                ],
            },
            {
                'title': 'Reading data',
                'tasks': [
                    'Use SELECT to read specific columns',
                    'Filter data with WHERE, AND, OR, IN, BETWEEN, and LIKE',
                    'Sort and limit results using ORDER BY and LIMIT',
                ],
            },
            {
                'title': 'Aggregations',
                'tasks': [
                    'Use COUNT, SUM, AVG, MIN, and MAX',
                    'Group records with GROUP BY',
                    'Filter grouped results with HAVING',
                ],
            },
            {
                'title': 'Joins',
                'tasks': [
                    'Understand relationships between tables',
                    'Practice INNER JOIN and LEFT JOIN',
                    'Query students with courses using two related tables',
                ],
            },
            {
                'title': 'Subqueries and constraints',
                'tasks': [
                    'Write simple subqueries inside WHERE',
                    'Learn NOT NULL, UNIQUE, PRIMARY KEY, and FOREIGN KEY',
                    'Design a small library database schema',
                ],
            },
        ],
    },
    'dbms': {
        'title': 'DBMS',
        'description': 'Core database management concepts: models, normalization, transactions, and indexing.',
        'concepts': [
            {
                'title': 'DBMS foundations',
                'tasks': [
                    'Understand what a DBMS is and why applications use databases',
                    'Compare file systems and database systems',
                    'Learn users, schemas, tables, records, and metadata',
                ],
            },
            {
                'title': 'Data models and ER diagrams',
                'tasks': [
                    'Understand entity, attribute, relationship, and cardinality',
                    'Draw an ER diagram for a college management system',
                    'Convert a simple ER diagram into relational tables',
                ],
            },
            {
                'title': 'Normalization',
                'tasks': [
                    'Understand data redundancy and anomalies',
                    'Learn 1NF, 2NF, and 3NF with examples',
                    'Normalize a student-course table step by step',
                ],
            },
            {
                'title': 'Transactions and concurrency',
                'tasks': [
                    'Learn ACID properties with real-world examples',
                    'Understand commit, rollback, and savepoint',
                    'Study basic locking and concurrency problems',
                ],
            },
            {
                'title': 'Indexing and storage',
                'tasks': [
                    'Understand why indexes speed up searches',
                    'Learn primary index and secondary index basics',
                    'Compare sequential access and indexed access',
                ],
            },
        ],
    },
}

STUDY_GUIDES = {
    'dsa': [
        {
            'read': [
                'A program solves a problem by taking input, processing it step by step, and producing output.',
                'Variables store values, conditions choose between paths, and loops repeat work until a goal is reached.',
                'Complexity describes how much time or memory an algorithm needs as input grows.',
                'Start by dry-running small examples before writing code; it reveals logic errors early.',
            ],
            'remember': ['Input', 'Output', 'Loop', 'Condition', 'Dry run', 'Time complexity'],
            'practice': [
                'Print numbers from 1 to n and count how many loop steps run.',
                'Find the largest of three numbers using conditions.',
                'Given n, print the sum of numbers from 1 to n.',
                'Dry-run a loop that prints even numbers from 2 to 20.',
                'Classify simple code examples as O(1), O(n), or O(n^2).',
            ],
        },
        {
            'read': [
                'An array stores values in order, and each value can be reached using its index.',
                'Traversal means visiting every item one by one; searching means checking items until a match is found.',
                'Two-pointer logic uses two positions, often left and right, to solve problems efficiently.',
                'Strings behave like arrays of characters in many beginner problems.',
            ],
            'remember': ['Index', 'Traversal', 'Search', 'Two pointers', 'Substring', 'Frequency'],
            'practice': [
                'Find the minimum and maximum value in an array.',
                'Reverse an array without using a second array.',
                'Check whether a string is a palindrome.',
                'Count how many times each character appears in a word.',
                'Check if two strings are anagrams.',
            ],
        },
        {
            'read': [
                'Recursion means a function solves a problem by calling itself with a smaller input.',
                'Every recursive function needs a base case, otherwise it will call forever.',
                'The call stack stores unfinished function calls until the base case returns.',
                'Backtracking tries a choice, explores it, then undoes the choice to try another path.',
            ],
            'remember': ['Base case', 'Recursive case', 'Call stack', 'Choice', 'Backtrack'],
            'practice': [
                'Write factorial using recursion.',
                'Print numbers from n to 1 recursively.',
                'Find the sum of an array recursively.',
                'Generate all subsets of [1, 2, 3].',
                'Generate all permutations of a three-letter string.',
            ],
        },
        {
            'read': [
                'A linked list stores data in nodes, and each node points to the next node.',
                'A stack follows Last In, First Out: the last item added is removed first.',
                'A queue follows First In, First Out: the first item added is removed first.',
                'These structures are useful when order of processing matters.',
            ],
            'remember': ['Node', 'Pointer', 'Head', 'Stack', 'Queue', 'LIFO', 'FIFO'],
            'practice': [
                'Insert a node at the beginning of a linked list.',
                'Delete a node by value from a linked list.',
                'Use a stack to check balanced brackets.',
                'Use a stack to reverse a string.',
                'Use a queue to process names in arrival order.',
            ],
        },
        {
            'read': [
                'A tree stores data in parent-child relationships, starting from a root node.',
                'A graph stores vertices connected by edges and can represent networks or maps.',
                'Binary search works only on sorted data and repeatedly halves the search area.',
                'Sorting algorithms arrange data; each sorting method has different speed and memory tradeoffs.',
            ],
            'remember': ['Root', 'Child', 'Traversal', 'Vertex', 'Edge', 'BFS', 'DFS', 'Binary search'],
            'practice': [
                'Perform inorder, preorder, and postorder traversal on a small tree.',
                'Search for a number using binary search.',
                'Sort an array using bubble sort.',
                'Trace merge sort on [5, 2, 8, 1].',
                'Run BFS and DFS on a small graph drawn on paper.',
            ],
        },
    ],
    'python': [
        {
            'read': [
                'Python code runs line by line, which makes it friendly for beginners.',
                'Variables are names that store values such as numbers, text, or true/false data.',
                'Use input() to receive text from the user and print() to show output.',
                'Type conversion changes data from one type to another, such as string to integer.',
            ],
            'remember': ['Variable', 'String', 'Integer', 'Float', 'Boolean', 'input()', 'print()'],
            'practice': [
                'Print your name and age.',
                'Take two numbers from the user and print their sum.',
                'Convert user input from string to integer.',
                'Calculate the area of a rectangle.',
                'Build a calculator for addition, subtraction, multiplication, and division.',
            ],
        },
        {
            'read': [
                'Conditions let a program choose what to do based on whether something is true or false.',
                'A for loop is useful when you know the sequence or range you want to repeat over.',
                'A while loop is useful when repetition depends on a condition.',
                'Use break to stop a loop and continue to skip to the next loop cycle.',
            ],
            'remember': ['if', 'elif', 'else', 'for', 'while', 'break', 'continue'],
            'practice': [
                'Check whether a number is positive, negative, or zero.',
                'Print the multiplication table of a number.',
                'Find the sum of even numbers from 1 to n.',
                'Keep asking for a password until the correct one is entered.',
                'Build a number guessing game.',
            ],
        },
        {
            'read': [
                'Lists store ordered values and can be changed after creation.',
                'Tuples store ordered values but are usually treated as fixed.',
                'Sets store unique values and are useful for removing duplicates.',
                'Dictionaries store key-value pairs, like a username connected to a password.',
            ],
            'remember': ['List', 'Tuple', 'Set', 'Dictionary', 'Index', 'Key', 'Value'],
            'practice': [
                'Store five marks in a list and find the average.',
                'Remove duplicate values using a set.',
                'Count word frequency using a dictionary.',
                'Find the highest mark from a list.',
                'Build a contact book with name and phone number.',
            ],
        },
        {
            'read': [
                'Functions group reusable logic under a name.',
                'Parameters receive input values and return sends a result back.',
                'Scope controls where a variable can be used.',
                'Modules let you split code into multiple files and reuse Python libraries.',
            ],
            'remember': ['Function', 'Parameter', 'Return', 'Scope', 'Import', 'Module'],
            'practice': [
                'Write a function to add two numbers.',
                'Write a function to check if a number is prime.',
                'Write a function that returns the largest item in a list.',
                'Create a file named helpers.py and import a function from it.',
                'Use the math module to calculate square root.',
            ],
        },
        {
            'read': [
                'Files help programs save data after the program stops running.',
                'Exceptions are errors that can be handled using try and except.',
                'A class is a blueprint, and an object is a real item created from that blueprint.',
                'Object-oriented code keeps related data and behavior together.',
            ],
            'remember': ['File', 'Read', 'Write', 'Exception', 'Class', 'Object', 'Method'],
            'practice': [
                'Write user notes to a text file.',
                'Read and print each line from a file.',
                'Handle division by zero using try and except.',
                'Create a Student class with name and marks.',
                'Create objects and call their methods.',
            ],
        },
    ],
    'sql': [
        {
            'read': [
                'A database stores organized data, usually inside tables.',
                'A table contains rows and columns; each row is one record.',
                'A primary key uniquely identifies each row.',
                'INSERT, UPDATE, and DELETE change data inside a table.',
            ],
            'remember': ['Table', 'Row', 'Column', 'Primary key', 'INSERT', 'UPDATE', 'DELETE'],
            'practice': [
                'Create a students table with id, name, age, and city.',
                'Insert five student records.',
                'Update one student city.',
                'Delete one student record.',
                'Select all records from the table.',
            ],
        },
        {
            'read': [
                'SELECT reads data from one or more tables.',
                'WHERE filters rows based on conditions.',
                'AND and OR combine multiple conditions.',
                'ORDER BY sorts output, and LIMIT restricts how many rows are returned.',
            ],
            'remember': ['SELECT', 'WHERE', 'AND', 'OR', 'LIKE', 'ORDER BY', 'LIMIT'],
            'practice': [
                'Select only student names from a table.',
                'Find students older than 18.',
                'Find students from Chennai or Hyderabad.',
                'Find names starting with A using LIKE.',
                'Show the youngest three students.',
            ],
        },
        {
            'read': [
                'Aggregate functions calculate one result from many rows.',
                'COUNT counts rows, AVG finds average, and SUM adds values.',
                'GROUP BY creates groups before aggregation.',
                'HAVING filters groups after aggregation.',
            ],
            'remember': ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP BY', 'HAVING'],
            'practice': [
                'Count total students.',
                'Find average marks.',
                'Find highest and lowest marks.',
                'Group students by city.',
                'Show cities that have more than two students.',
            ],
        },
        {
            'read': [
                'Joins combine rows from two related tables.',
                'An INNER JOIN returns matching records from both tables.',
                'A LEFT JOIN returns all rows from the left table and matching rows from the right table.',
                'Foreign keys connect one table to another.',
            ],
            'remember': ['INNER JOIN', 'LEFT JOIN', 'Foreign key', 'Relationship', 'ON'],
            'practice': [
                'Create students and courses tables.',
                'Create enrollments using student_id and course_id.',
                'List each student with their course name.',
                'Show all students even if they have no course.',
                'Find students enrolled in Python.',
            ],
        },
        {
            'read': [
                'A subquery is a query inside another query.',
                'Constraints protect data quality by enforcing rules.',
                'NOT NULL prevents empty values and UNIQUE prevents duplicates.',
                'Foreign key constraints protect relationships between tables.',
            ],
            'remember': ['Subquery', 'Constraint', 'NOT NULL', 'UNIQUE', 'FOREIGN KEY'],
            'practice': [
                'Find students with marks above the average.',
                'Create a table with NOT NULL name.',
                'Create a UNIQUE email column.',
                'Create a foreign key between two tables.',
                'Design tables for a small library system.',
            ],
        },
    ],
    'dbms': [
        {
            'read': [
                'A DBMS is software used to store, manage, and retrieve data safely.',
                'Databases are better than plain files when many users or relationships are involved.',
                'Schemas define structure, while data records store actual values.',
                'Metadata is data about data, such as table names and column types.',
            ],
            'remember': ['DBMS', 'Database', 'Schema', 'Record', 'Metadata', 'User'],
            'practice': [
                'List five apps that use databases.',
                'Compare storing marks in a file versus a database.',
                'Identify tables needed for a college system.',
                'Write sample records for a students table.',
                'Explain metadata using one table example.',
            ],
        },
        {
            'read': [
                'An entity is a real-world object such as Student, Course, or Teacher.',
                'Attributes describe an entity, such as name or age.',
                'Relationships connect entities, such as Student enrolls in Course.',
                'Cardinality explains how many records can participate in a relationship.',
            ],
            'remember': ['Entity', 'Attribute', 'Relationship', 'Cardinality', 'ER diagram'],
            'practice': [
                'Identify entities for a college system.',
                'List attributes for Student and Course.',
                'Draw Student enrolls in Course relationship.',
                'Mark one-to-one, one-to-many, and many-to-many examples.',
                'Convert a simple ER diagram into tables.',
            ],
        },
        {
            'read': [
                'Normalization organizes tables to reduce duplicate data.',
                '1NF removes repeating groups and stores atomic values.',
                '2NF removes partial dependency from composite keys.',
                '3NF removes transitive dependency between non-key columns.',
            ],
            'remember': ['Redundancy', 'Anomaly', '1NF', '2NF', '3NF', 'Dependency'],
            'practice': [
                'Find duplicate data in a student-course table.',
                'Convert repeating subject columns into separate rows.',
                'Split student and course data into separate tables.',
                'Identify update, insert, and delete anomalies.',
                'Normalize one messy table up to 3NF.',
            ],
        },
        {
            'read': [
                'A transaction is a group of database operations treated as one unit.',
                'ACID means Atomicity, Consistency, Isolation, and Durability.',
                'COMMIT saves a transaction and ROLLBACK cancels it.',
                'Concurrency control prevents users from corrupting each other\'s data.',
            ],
            'remember': ['Transaction', 'ACID', 'COMMIT', 'ROLLBACK', 'Lock', 'Concurrency'],
            'practice': [
                'Explain money transfer as a transaction.',
                'Write what should happen if one step of transfer fails.',
                'Give an example for each ACID property.',
                'Explain commit and rollback in your own words.',
                'Describe why two users editing the same data can be risky.',
            ],
        },
        {
            'read': [
                'An index is a helper structure that makes searching faster.',
                'Indexes improve reads but can slow down inserts and updates because the index must also change.',
                'Primary indexes are based on primary keys.',
                'Secondary indexes help search by non-primary columns.',
            ],
            'remember': ['Index', 'Primary index', 'Secondary index', 'Search', 'Storage'],
            'practice': [
                'Explain an index using a book index example.',
                'Choose which column to index in a students table.',
                'Compare searching with and without an index.',
                'List one advantage and one disadvantage of indexes.',
                'Draw how sorted index values point to records.',
            ],
        },
    ],
}

COURSE_ALIASES = {
    'data structures and algorithms': 'dsa',
    'data structure and algorithm': 'dsa',
    'dsa': 'dsa',
    'python': 'python',
    'python programming': 'python',
    'sql': 'sql',
    'dbms': 'dbms',
    'database management system': 'dbms',
    'database management systems': 'dbms',
}

def course_slug(title):
    normalized = ' '.join(title.strip().lower().split())
    return COURSE_ALIASES.get(normalized)

def get_curriculum(course):
    slug = course_slug(course.title)
    if not slug:
        return None
    return CURRICULUM[slug]

def curriculum_task_ids(curriculum):
    task_ids = []
    for concept_index, concept in enumerate(curriculum['concepts']):
        for task_index, _ in enumerate(concept['tasks']):
            task_ids.append(f'{concept_index}-{task_index}')
    return task_ids

def get_task_context(course, task_id):
    curriculum = get_curriculum(course)
    slug = course_slug(course.title)

    if not curriculum or not slug or task_id not in curriculum_task_ids(curriculum):
        return None

    concept_index_text, task_index_text = task_id.split('-', 1)
    concept_index = int(concept_index_text)
    task_index = int(task_index_text)
    concept = curriculum['concepts'][concept_index]
    guide = STUDY_GUIDES[slug][concept_index]

    return {
        'curriculum': curriculum,
        'slug': slug,
        'concept': concept,
        'concept_number': concept_index + 1,
        'task_id': task_id,
        'task_title': concept['tasks'][task_index],
        'read': guide['read'],
        'remember': guide['remember'],
        'practice': guide['practice'],
    }

def recalculate_course_progress(course):
    curriculum = get_curriculum(course)
    if not curriculum:
        return

    task_ids = curriculum_task_ids(curriculum)
    if not task_ids:
        course.progress = 0
        course.status = 'Not Started'
        return

    completed_count = TaskProgress.query.filter_by(
        user_id=current_user.id,
        course_id=course.id,
        completed=True,
    ).filter(TaskProgress.task_id.in_(task_ids)).count()

    course.progress = round((completed_count / len(task_ids)) * 100)

    if course.progress == 100:
        course.status = 'Completed'
    elif course.progress > 0:
        course.status = 'In Progress'
    else:
        course.status = 'Not Started'

def decorate_course(course):
    curriculum = get_curriculum(course)
    course.curriculum = curriculum
    course.slug = course_slug(course.title)
    course.task_total = len(curriculum_task_ids(curriculum)) if curriculum else 0
    course.task_done = 0

    if curriculum:
        course.task_done = TaskProgress.query.filter_by(
            user_id=current_user.id,
            course_id=course.id,
            completed=True,
        ).count()

    return course

def initialize_database():
    db.create_all()

    inspector = inspect(db.engine)
    if not inspector.has_table('course'):
        return

    course_columns = [column['name'] for column in inspector.get_columns('course')]
    if 'user_id' in course_columns:
        return

    with db.engine.begin() as connection:
        connection.execute(text('ALTER TABLE course ADD COLUMN user_id INTEGER'))
        first_user_id = connection.execute(
            text('SELECT id FROM "user" ORDER BY id LIMIT 1')
        ).scalar()

        if first_user_id:
            connection.execute(
                text('UPDATE course SET user_id = :user_id WHERE user_id IS NULL'),
                {'user_id': first_user_id},
            )

with app.app_context():
    initialize_database()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Home
@app.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'All')
    search_query = request.args.get('q', '').strip()

    all_courses = Course.query.filter_by(user_id=current_user.id).order_by(Course.id.desc()).all()
    for course in all_courses:
        recalculate_course_progress(course)
        decorate_course(course)
    db.session.commit()

    courses = all_courses

    if status_filter != 'All':
        courses = [course for course in courses if course.status == status_filter]

    if search_query:
        courses = [
            course for course in courses
            if search_query.lower() in course.title.lower()
        ]

    total_courses = len(all_courses)
    completed_courses = sum(1 for course in all_courses if course.status == 'Completed')
    active_courses = sum(1 for course in all_courses if course.status == 'In Progress')
    average_progress = round(
        sum(course.progress for course in all_courses) / total_courses
    ) if total_courses else 0

    stats = {
        'total': total_courses,
        'completed': completed_courses,
        'active': active_courses,
        'average_progress': average_progress,
    }
    user_course_slugs = {course.slug for course in all_courses if course.slug}
    recommended_tracks = [
        {
            'slug': slug,
            'title': curriculum['title'],
            'description': curriculum['description'],
            'concept_count': len(curriculum['concepts']),
            'task_count': len(curriculum_task_ids(curriculum)),
            'is_added': slug in user_course_slugs,
        }
        for slug, curriculum in CURRICULUM.items()
    ]

    return render_template(
        'index.html',
        courses=courses,
        stats=stats,
        status_filter=status_filter,
        search_query=search_query,
        recommended_tracks=recommended_tracks,
    )

@app.route('/healthz')
def healthz():
    return {'status': 'ok'}

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.form['username'].strip()
        raw_password = request.form['password']

        if len(username) < 3:
            flash("Username must be at least 3 characters")
            return redirect('/register')

        if len(raw_password) < 6:
            flash("Password must be at least 6 characters")
            return redirect('/register')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect('/register')

        password = generate_password_hash(raw_password)

        user = User(username=username, password=password)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username already exists")
            return redirect('/register')
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception("Registration failed")
            flash("Registration failed. Please try again.")
            return redirect('/register')

        flash("Registration successful. Please login.")
        return redirect('/login')

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':

        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')

        flash("Invalid Username or Password")

    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# Add Course
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        title = request.form['title'].strip()

        if not title:
            flash("Course name is required")
            return redirect('/add')

        slug = course_slug(title)
        if slug:
            title = CURRICULUM[slug]['title']

        existing_course = Course.query.filter_by(user_id=current_user.id, title=title).first()
        if existing_course:
            flash("This course is already in your dashboard")
            return redirect(f'/course/{existing_course.id}')

        course = Course(
            title=title,
            user_id=current_user.id
        )

        db.session.add(course)
        db.session.commit()

        return redirect('/')

    return render_template('add_course.html')

@app.route('/add/predefined/<slug>', methods=['POST'])
@login_required
def add_predefined_course(slug):
    curriculum = CURRICULUM.get(slug)
    if not curriculum:
        flash("Course not found")
        return redirect('/')

    existing_course = Course.query.filter_by(
        user_id=current_user.id,
        title=curriculum['title'],
    ).first()

    if existing_course:
        flash("This course is already in your dashboard")
        return redirect(f'/course/{existing_course.id}')

    course = Course(
        title=curriculum['title'],
        progress=0,
        status='Not Started',
        user_id=current_user.id,
    )
    db.session.add(course)
    db.session.commit()

    flash(f"{curriculum['title']} roadmap added")
    return redirect(f'/course/{course.id}')

@app.route('/course/<int:id>')
@login_required
def course_detail(id):
    course = db.session.get(Course, id)

    if not course or course.user_id != current_user.id:
        return redirect('/')

    curriculum = get_curriculum(course)
    if not curriculum:
        flash("This custom course does not have a built-in task roadmap yet")
        return redirect('/')

    recalculate_course_progress(course)
    db.session.commit()

    completed_tasks = {
        task.task_id
        for task in TaskProgress.query.filter_by(
            user_id=current_user.id,
            course_id=course.id,
            completed=True,
        ).all()
    }

    concepts = []
    for concept_index, concept in enumerate(curriculum['concepts']):
        tasks = []
        for task_index, task_title in enumerate(concept['tasks']):
            task_id = f'{concept_index}-{task_index}'
            tasks.append({
                'id': task_id,
                'title': task_title,
                'completed': task_id in completed_tasks,
                'url': f'/course/{course.id}/task/{task_id}',
            })

        concepts.append({
            'number': concept_index + 1,
            'title': concept['title'],
            'tasks': tasks,
            'completed_count': sum(1 for task in tasks if task['completed']),
        })

    return render_template(
        'course_detail.html',
        course=course,
        curriculum=curriculum,
        concepts=concepts,
        total_tasks=len(curriculum_task_ids(curriculum)),
        completed_tasks=len(completed_tasks),
    )

@app.route('/course/<int:course_id>/task/<task_id>')
@login_required
def task_detail(course_id, task_id):
    course = db.session.get(Course, course_id)

    if not course or course.user_id != current_user.id:
        return redirect('/')

    task_context = get_task_context(course, task_id)
    if not task_context:
        flash("Task not found")
        return redirect(f'/course/{course.id}')

    task_progress = TaskProgress.query.filter_by(
        user_id=current_user.id,
        course_id=course.id,
        task_id=task_id,
        completed=True,
    ).first()

    recalculate_course_progress(course)
    db.session.commit()

    return render_template(
        'task_detail.html',
        course=course,
        task=task_context,
        is_completed=bool(task_progress),
    )

@app.route('/course/<int:course_id>/task/<task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(course_id, task_id):
    course = db.session.get(Course, course_id)

    if not course or course.user_id != current_user.id:
        return redirect('/')

    task_context = get_task_context(course, task_id)
    if not task_context:
        flash("Task not found")
        return redirect(f'/course/{course.id}')

    task_progress = TaskProgress.query.filter_by(
        user_id=current_user.id,
        course_id=course.id,
        task_id=task_id,
    ).first()

    if not task_progress:
        task_progress = TaskProgress(
            user_id=current_user.id,
            course_id=course.id,
            task_id=task_id,
            completed=True,
        )
        db.session.add(task_progress)
    else:
        task_progress.completed = not task_progress.completed

    recalculate_course_progress(course)
    db.session.commit()

    return redirect(request.form.get('next') or f'/course/{course.id}')

# Update Course
@app.route('/update/<int:id>', methods=['POST'])
@login_required
def update_course(id):

    course = db.session.get(Course, id)

    if not course or course.user_id != current_user.id:
        return redirect('/')

    if get_curriculum(course):
        recalculate_course_progress(course)
        db.session.commit()
        flash("Progress for this course updates automatically from completed tasks")
        return redirect(f'/course/{course.id}')

    try:
        progress = int(request.form['progress'])
    except ValueError:
        flash("Progress must be a number")
        return redirect('/')

    progress = max(0, min(progress, 100))

    if progress == 100:
        course.status = "Completed"
    elif progress > 0:
        course.status = "In Progress"
    else:
        course.status = "Not Started"

    course.progress = progress

    db.session.commit()

    return redirect('/')

# Delete Course
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_course(id):

    course = db.session.get(Course, id)

    if course and course.user_id == current_user.id:
        TaskProgress.query.filter_by(
            user_id=current_user.id,
            course_id=course.id,
        ).delete()
        db.session.delete(course)
        db.session.commit()

    return redirect('/')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG') == '1')
