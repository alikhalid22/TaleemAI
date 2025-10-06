import sqlite3
import curriculum_handler as ch # NEW: Required for the deep preparation logic

DB_NAME = "taleemai.db"

def init_db():
    """Initializes the database and creates/upgrades tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create the 'users' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE
    )
    """)

    # Create the 'quiz_history' table with all necessary columns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        board TEXT NOT NULL,
        grade TEXT NOT NULL,
        subject TEXT NOT NULL,
        topic TEXT NOT NULL,
        question TEXT NOT NULL,
        user_answer TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        is_correct BOOLEAN NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)
    conn.commit()
    conn.close()

def get_user(username):
    """Finds a user by their username, ignoring case."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.lower(),))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username):
    """Adds a new user to the database with a lowercase username."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username) VALUES (?)", (username.lower(),))
    new_user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_user_id

def save_quiz_results(user_id, context, selected_topic, questions, user_answers):
    """Saves the results of a completed quiz to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    for i, question_data in enumerate(questions):
        user_answer = user_answers[i]
        correct_answer = question_data["correct_answer"]
        is_correct = (user_answer == correct_answer)
        
        cursor.execute("""
        INSERT INTO quiz_history (user_id, board, grade, subject, topic, question, user_answer, correct_answer, is_correct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            context['board'],
            context['grade'],
            context['subject'],
            selected_topic,
            question_data["question"],
            user_answer,
            correct_answer,
            is_correct
        ))
    
    conn.commit()
    conn.close()
    print(f"--- DEV LOG: Saved {len(questions)} quiz results for user_id {user_id} ---")


def get_distinct_classes_for_user(user_id):
    """Finds all unique Board-Grade combinations a user has been quizzed on."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT board, grade FROM quiz_history WHERE user_id = ?", (user_id,))
    classes = cursor.fetchall()
    conn.close()
    return [{'board': row[0], 'grade': row[1]} for row in classes]

def get_most_recent_class(user_id):
    """Finds the most recent Board and Grade a user was quizzed on."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT board, grade FROM quiz_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
    recent_class = cursor.fetchone()
    conn.close()
    return {'board': recent_class[0], 'grade': recent_class[1]} if recent_class else None

def get_deep_subject_preparation(user_id, board, grade):
    """
    Calculates the 'True Curriculum Mastery' percentage for each subject in a class.
    """
    subjects = ch.get_subjects_for_grade(board, grade)
    performance = {}
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for subject in subjects:
        # 1. Get the DENOMINATOR: Total topics for this subject from curriculum.json
        total_topics = ch.count_topics_for_subject(board, grade, subject)
        if total_topics == 0:
            performance[subject] = 0.0
            continue

        # 2. Get the NUMERATOR: Find all topics the user has "mastered" (scored >= 70%)
        cursor.execute("""
            SELECT topic
            FROM quiz_history
            WHERE user_id = ? AND board = ? AND grade = ? AND subject = ?
            GROUP BY topic
            HAVING AVG(is_correct) >= 0.70
        """, (user_id, board, grade, subject))
        
        mastered_topics = cursor.fetchall()
        count_mastered = len(mastered_topics)
        
        # 3. Calculate the True Mastery Percentage
        mastery_percentage = (count_mastered / total_topics) * 100
        performance[subject] = mastery_percentage

    conn.close()
    return performance

def get_weakest_topics_for_subject(user_id, board, grade, subject, limit=3):
    """Finds the weakest topics for a specific subject within a specific class."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT topic, COUNT(*) as incorrect_count
    FROM quiz_history
    WHERE user_id = ? AND board = ? AND grade = ? AND subject = ? AND is_correct = 0
    GROUP BY topic
    ORDER BY incorrect_count DESC
    LIMIT ?
    """, (user_id, board, grade, subject, limit))
    weak_topics = [row[0] for row in cursor.fetchall()]
    conn.close()
    return weak_topics