import streamlit as st
import database as db
import curriculum_handler as ch
import ai_handler as ai

# --- Initialize Database & Page Config ---
db.init_db()
st.set_page_config(page_title="TaleemAI", page_icon="🎓", layout="centered")

def load_css(file_name):
    with open(file_name) as f: st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css("style/style.css")

# --- Session State Management ---
def initialize_session_state():
    # A single function to reset the app to its login state
    st.session_state.clear()
    st.session_state.page = "login"

# Initialize state on the very first run
if 'page' not in st.session_state:
    initialize_session_state()

# --- Page Router ---
# This structure ensures only one page's code runs at a time.

# --- Page 1: Login/Signup ---
if st.session_state.page == "login":
    st.title("🎓 Welcome to TaleemAI")
    st.subheader("Your Personal AI Learning Companion")
    with st.form("login_form"):
        username_input = st.text_input("Enter your Username")
        submitted = st.form_submit_button("Continue", type="primary")
        if submitted:
            if not username_input:
                st.warning("Please enter a username.")
            else:
                user_in_db = db.get_user(username_input)
                if user_in_db:
                    st.session_state.user_info = {'id': user_in_db[0], 'username': user_in_db[1]}
                    st.session_state.page = "welcome_back"
                    st.rerun()
                else:
                    new_user_id = db.create_user(username_input)
                    st.session_state.user_info = {'id': new_user_id, 'username': username_input.lower()}
                    st.session_state.page = "dashboard"
                    st.rerun()

# --- Intermediate Welcome Back Page ---
elif st.session_state.page == "welcome_back":
    st.success(f"Welcome back, {st.session_state.user_info['username']}!")
    if st.button("Go to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

# --- Page 2: Main Dashboard ---
elif st.session_state.page == "dashboard":
    st.title("Dashboard")
    st.header(f"Welcome, {st.session_state.user_info['username'].capitalize()}!")
    
    user_id = st.session_state.user_info['id']
    user_classes = db.get_distinct_classes_for_user(user_id)

    if not user_classes:
        st.info("Your personalized dashboard will appear here once you complete your first quiz!")
    else:
        st.subheader("📊 Your Progress Report")
        class_options = [f"{c['board']} - {c['grade']}" for c in user_classes]
        
        most_recent_class = db.get_most_recent_class(user_id)
        default_index = 0
        if most_recent_class:
            most_recent_class_str = f"{most_recent_class['board']} - {most_recent_class['grade']}"
            if most_recent_class_str in class_options:
                default_index = class_options.index(most_recent_class_str)

        selected_class_str = st.selectbox("Show Progress For:", class_options, index=default_index)
        
        selected_board, selected_grade = selected_class_str.split(' - ')
        st.markdown("---")
        
        # --- THIS IS THE KEY CHANGE ---
        # Call our new, powerful function
        subject_preparation = db.get_deep_subject_preparation(user_id, selected_board, selected_grade)
        
        if subject_preparation:
            # Calculate overall percentage based on the new "True Mastery" scores
            overall_preparation = sum(subject_preparation.values()) / len(subject_preparation)
            st.metric(label=f"Overall Preparation for {selected_grade}", value=f"{overall_preparation:.1f}%")
            
            st.markdown("---")
            st.subheader("Subject Preparation")
            sorted_subjects = sorted(subject_preparation.items(), key=lambda item: item[1])
            
            for subject, percentage in sorted_subjects:
                with st.expander(f"{subject} - Preparation: {percentage:.1f}%"):
                    # The weak topics function already works perfectly with this
                    weak_topics = db.get_weakest_topics_for_subject(user_id, selected_board, selected_grade, subject)
                    if weak_topics:
                        st.write("**Topics to Focus On:**")
                        for topic in weak_topics:
                            if st.button(f"Study '{topic}'", key=f"study_{subject}_{topic}"):
                                st.session_state.prep_context = {'board': selected_board, 'grade': selected_grade, 'subject': subject}
                                st.session_state.selected_topic = topic
                                st.session_state.source_page = "dashboard"
                                st.session_state.page = "learning_core"
                                st.rerun()
                    else:
                        st.success("You haven't shown any specific weaknesses in this subject yet. Keep practicing!")

    # --- Standard Navigation ---
    st.markdown("---")
    st.subheader("Start a New Session")
    if st.button("📚 Class Preparation", use_container_width=True, type="primary", key="dash_class_prep"):
        st.session_state.prep_context = {}
        st.session_state.page = "class_prep"
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Logout", key="logout_dashboard"):
        initialize_session_state()
        st.rerun()
# --- Page 3: Class Preparation Wizard ---
elif st.session_state.page == "class_prep":
    st.title("📚 Class Preparation")
    
    # Use a variable to track the current step in the wizard
    if 'prep_step' not in st.session_state:
        st.session_state.prep_step = 1

    # Step 1: Select Board, Grade, & Subject
    if st.session_state.prep_step == 1:
        st.header("Step 1: Select Your Textbook")
        
        # THIS IS THE CORRECTED, DEPENDENT LOGIC
        boards = ch.get_boards()
        board = st.selectbox("Select Board:", boards)
        
        grades = ch.get_grades(board)
        grade = st.selectbox("Select Grade:", grades)
        
        subjects = ch.get_subjects_for_grade(board, grade)
        subject = st.selectbox("Select Subject:", subjects)

        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state.prep_context = {'board': board, 'grade': grade, 'subject': subject}
            st.session_state.prep_step = 2
            st.rerun()
            
        st.markdown("---")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

    # Step 2: Select Chapter
    elif st.session_state.prep_step == 2:
        st.header("Step 2: Select a Chapter")
        context = st.session_state.prep_context
        chapters = ch.get_chapters_for_subject(context['board'], context['grade'], context['subject'])
        selected_chapter = st.radio("Chapters:", chapters, index=None)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.prep_step = 1
                st.rerun()
        with col2:
            if st.button("Next →", type="primary", use_container_width=True, disabled=(selected_chapter is None)):
                st.session_state.prep_context['chapter'] = selected_chapter
                st.session_state.prep_step = 3
                st.rerun()

    # Step 3: Select Topic
    elif st.session_state.prep_step == 3:
        st.header(f"Step 3: Select a Topic")
        context = st.session_state.prep_context
        topics = ch.get_topics_for_chapter(context['board'], context['grade'], context['subject'], context['chapter'])
        selected_topic = st.radio("Topics:", topics, index=None)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.prep_step = 2
                st.rerun()
        with col2:
            if st.button("Start Learning →", type="primary", use_container_width=True, disabled=(selected_topic is None)):
                st.session_state.selected_topic = selected_topic
                st.session_state.source_page = "class_prep"
                st.session_state.page = "learning_core"
                # Reset learning core state for a clean start
                st.session_state.learning_mode = None
                st.rerun()

# --- Page 4: Unified Learning Core (Stable Placeholder) ---
elif st.session_state.page == "learning_core":
    st.title(f"🚀 Learning: {st.session_state.get('selected_topic', 'N/A')}")
    
    # Helper function to display explanations
    def display_explanation(exp_title, exp_content):
        st.subheader(exp_title)
        lang = st.session_state.get("explanation_lang", "English")
        if lang == "Urdu":
            st.markdown(f'<div class="urdu-font">{exp_content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(exp_content)

    # Initialize learning mode if not set
    if 'learning_mode' not in st.session_state or st.session_state.learning_mode is None:
        st.subheader("How would you like to start?")
        st.session_state.explanation_lang = st.selectbox("Choose explanation language:", ["English", "Roman Urdu", "Urdu"])
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Summary", use_container_width=True):
                with st.spinner("Generating..."): st.session_state.summary_exp = ai.explain_topic_summary(st.session_state.prep_context, st.session_state.selected_topic, st.session_state.explanation_lang)
                st.session_state.learning_mode = 'explaining'; st.rerun()
        with col2:
            if st.button("Explain in Detail", use_container_width=True):
                with st.spinner("Generating..."): st.session_state.detailed_exp = ai.explain_topic_detailed(st.session_state.prep_context, st.session_state.selected_topic, st.session_state.explanation_lang)
                st.session_state.learning_mode = 'explaining'; st.rerun()
        with col3:
            if st.button("Deep Detail", use_container_width=True):
                with st.spinner("Generating..."): st.session_state.deep_detail_exp = ai.explain_topic_deep_detail(st.session_state.prep_context, st.session_state.selected_topic, st.session_state.explanation_lang)
                st.session_state.learning_mode = 'explaining'; st.rerun()

    # Explanation Hub
    elif st.session_state.learning_mode == 'explaining':
        if st.session_state.get("summary_exp"): display_explanation("Summary", st.session_state.summary_exp)
        if st.session_state.get("detailed_exp"): display_explanation("Detailed Explanation", st.session_state.detailed_exp)
        if st.session_state.get("deep_detail_exp"): display_explanation("Deep Detail Explanation", st.session_state.deep_detail_exp)
        if st.session_state.get("example_exp"): display_explanation("Real-World Example", st.session_state.example_exp)
        
        st.markdown("---"); st.subheader("What's next?")
        cols = st.columns(4)
        if not st.session_state.get("example_exp"):
            if cols[0].button("🌍 Give me an Example", use_container_width=True):
                with st.spinner("Thinking..."): st.session_state.example_exp = ai.generate_real_world_example(st.session_state.prep_context, st.session_state.selected_topic, st.session_state.explanation_lang)
                st.rerun()
        if not st.session_state.get("detailed_exp"):
            if cols[1].button("📖 Explain in Detail", use_container_width=True):
                with st.spinner("Generating..."): st.session_state.detailed_exp = ai.explain_topic_detailed(st.session_state.prep_context, st.session_state.selected_topic, st.session_state.explanation_lang)
                st.rerun()
        if not st.session_state.get("deep_detail_exp"):
            if cols[2].button("🔬 Deep Detail", use_container_width=True):
                with st.spinner("Generating..."): st.session_state.deep_detail_exp = ai.explain_topic_deep_detail(st.session_state.prep_context, st.session_state.selected_topic, st.session_state.explanation_lang)
                st.rerun()
        
        with st.form("follow_up_form"):
            follow_up_question = st.text_area("I didn't understand...")
            submitted = st.form_submit_button("Ask")
            if submitted and follow_up_question:
                context_explanation = st.session_state.get("deep_detail_exp") or st.session_state.get("detailed_exp") or st.session_state.get("summary_exp")
                with st.spinner("Thinking..."): st.session_state.follow_up_answer = ai.answer_follow_up(st.session_state.prep_context, st.session_state.selected_topic, context_explanation, follow_up_question, st.session_state.explanation_lang)
        
        if st.session_state.get("follow_up_answer"):
            st.info("Tutor's Answer:")
            if st.session_state.explanation_lang == "Urdu": st.markdown(f'<div class="urdu-font">{st.session_state.follow_up_answer}</div>', unsafe_allow_html=True)
            else: st.write(st.session_state.follow_up_answer)
        
        st.markdown("---")
        if st.button("✅ Test me on this Topic", type="primary", use_container_width=True):
            with st.spinner("Preparing quiz..."): quiz = ai.generate_topic_quiz(st.session_state.prep_context, st.session_state.selected_topic)
            if quiz: st.session_state.quiz_questions = quiz; st.session_state.current_quiz_question = 0; st.session_state.quiz_answers = [None] * len(quiz); st.session_state.learning_mode = 'quiz'; st.rerun()
            else: st.error("Our AI Tutor is busy.")

    # Quiz Flow
    elif st.session_state.learning_mode == 'quiz':
        st.subheader("Topic Quiz")
        index = st.session_state.current_quiz_question
        question_data = st.session_state.quiz_questions[index]
        st.write(f"**Question {index + 1}/{len(st.session_state.quiz_questions)}**")
        st.write(question_data["question"])
        with st.form(key=f"quiz_form_{index}"):
            user_choice = st.radio("Options:", question_data["options"], index=None, label_visibility="collapsed")
            submitted = st.form_submit_button("Next Question →")
            if submitted:
                if user_choice:
                    st.session_state.quiz_answers[index] = user_choice
                    if index < len(st.session_state.quiz_questions) - 1:
                        st.session_state.current_quiz_question += 1
                    else:
                        st.session_state.learning_mode = 'quiz_results'
                    st.rerun()
                else:
                    st.warning("Please select an answer.")

    # Quiz Results Flow
    elif st.session_state.learning_mode == 'quiz_results':
        st.subheader("Quiz Results"); st.balloons()
        db.save_quiz_results(user_id=st.session_state.user_info['id'], context=st.session_state.prep_context, selected_topic=st.session_state.selected_topic, questions=st.session_state.quiz_questions, user_answers=st.session_state.quiz_answers)
        score = sum(1 for i, ua in enumerate(st.session_state.quiz_answers) if ua == st.session_state.quiz_questions[i]["correct_answer"])
        total = len(st.session_state.quiz_questions)
        st.metric(label="Your Score", value=f"{score}/{total}", delta=f"{(score/total)*100:.1f}%")
        st.markdown("---"); st.subheader("Detailed Review")
        for i, q_data in enumerate(st.session_state.quiz_questions):
            st.write(f"**Question {i+1}: {q_data['question']}**")
            user_ans = st.session_state.quiz_answers[i]
            correct_ans = q_data['correct_answer']
            if user_ans == correct_ans: st.markdown(f"✔️ Your answer: <span style='color:green;'>{user_ans}</span> (Correct)", unsafe_allow_html=True)
            else: st.markdown(f"❌ Your answer: <span style='color:red;'>{user_ans}</span> (Incorrect)", unsafe_allow_html=True); st.markdown(f"✔️ Correct answer: <span style='color:green;'>{correct_ans}</span>", unsafe_allow_html=True)
            with st.expander("💡 See Explanation"): st.write(q_data['explanation'])
            st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Test Again", use_container_width=True):
                st.session_state.learning_mode = 'quiz'; st.session_state.current_quiz_question = 0; st.session_state.quiz_answers = [None] * len(st.session_state.quiz_questions); st.rerun()
        with col2:
            if st.button("Learn Another Topic", use_container_width=True, type="primary"):
                st.session_state.page = st.session_state.source_page
                st.session_state.learning_mode = None
                st.rerun()

    # Back button for the whole learning core
    st.markdown("---")
    if st.button("← Go Back"):
        keys_to_reset = ['learning_mode', 'summary_exp', 'detailed_exp', 'deep_detail_exp', 'example_exp', 'follow_up_answer', 'quiz_questions']
        for key in keys_to_reset:
            if key in st.session_state:
                st.session_state[key] = None
        st.session_state.page = st.session_state.source_page
        st.rerun()