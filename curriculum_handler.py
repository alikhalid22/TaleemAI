import json

def load_curriculum():
    """Loads the entire curriculum from the JSON file."""
    with open('curriculum.json', 'r', encoding='utf-8') as f:
        return json.load(f)

CURRICULUM = load_curriculum()

def get_boards():
    """Returns a list of all available boards from the curriculum."""
    return list(CURRICULUM.keys())

def get_grades(board):
    """Returns a list of all available grades for a specific board."""
    if board in CURRICULUM:
        return list(CURRICULUM[board].keys())
    return []

def get_subjects_for_grade(board, grade):
    """Returns a list of subjects for a given board and grade."""
    if board in CURRICULUM and grade in CURRICULUM[board]:
        return list(CURRICULUM[board][grade].keys())
    return []

def get_chapters_for_subject(board, grade, subject):
    """Returns a list of chapters for a given board, grade, and subject."""
    if board in CURRICULUM and grade in CURRICULUM[board] and subject in CURRICULUM[board][grade]:
        return list(CURRICULUM[board][grade][subject].keys())
    return []

def get_topics_for_chapter(board, grade, subject, chapter):
    """Returns a list of topics for a given chapter."""
    if board in CURRICULUM and grade in CURRICULUM[board] and subject in CURRICULUM[board][grade] and chapter in CURRICULUM[board][grade][subject]:
        return CURRICULUM[board][grade][subject][chapter]
    return []
def count_topics_for_subject(board, grade, subject):
    """Counts the total number of topics for a given subject in the curriculum."""
    try:
        chapters = CURRICULUM[board][grade][subject]
        # Sum the number of topics in each chapter
        total_topics = sum(len(topics) for topics in chapters.values())
        return total_topics
    except KeyError:
        # If the subject/grade doesn't exist in the JSON, return 0
        return 0