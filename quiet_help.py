import os
import logging
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Setup logging
logging.basicConfig(level=logging.INFO)

# Constants for conversation states
CHOOSING_MAJOR, CHOOSING_SEMESTER, ASKING_QUESTION, CHOOSING_CLASS = range(4)

# Storage for user data (in-memory for demo, replace with persistent storage for production)
USER_DATA_FILE = 'user_data.json'
QUESTION_COUNT_FILE = 'question_count.json'

majors = [
    "Software Engineering", "Cyber Security", "AI & Robotics",
    "Mechanical Engineering", "Chemical & Materials Engineering",
    "Applied Mathematics", "Economics & Data Science", "Pedagogy",
    "Industrial Management"
]

classes_by_major_semester = {
    "Software Engineering": {
        "1": ["Intro to Programming", "Math 1", "English 1"],
        "2": ["OOP", "Data Structures", "Math 2"],
        "3": ["Algorithms", "Database Systems", "Computer Architecture"],
        "4": ["Operating Systems", "Web Technologies", "Discrete Mathematics"],
        "5": ["Software Engineering", "Mobile App Development", "Networks"],
        "6": ["Software Project Management", "Machine Learning", "Cloud Computing"],
        "7": ["Distributed Systems", "Cybersecurity", "AI Fundamentals"],
        "8": ["Capstone Project", "DevOps", "Advanced Software Design"]
    },
    "Cyber Security": {
        "1": ["Intro to IT", "Math 1", "English 1"],
        "2": ["Networking Basics", "Cryptography", "Math 2"],
        "3": ["System Security", "Linux Basics", "Data Structures"],
        "4": ["Web Security", "Malware Analysis", "Network Security"],
        "5": ["Security Audit", "Python for Security", "Cyber Law"],
        "6": ["Digital Forensics", "Cloud Security", "Penetration Testing"],
        "7": ["Secure Coding", "Incident Response", "Ethical Hacking"],
        "8": ["Capstone Project", "Advanced Threat Detection", "Security Management"]
    },
    "AI & Robotics": {
        "1": ["Intro to Programming", "Math 1", "English 1"],
        "2": ["OOP", "Linear Algebra", "Data Structures"],
        "3": ["Probability & Statistics", "Control Systems", "Robotics Fundamentals"],
        "4": ["Machine Learning", "Computer Vision", "AI Ethics"],
        "5": ["Deep Learning", "Robot Kinematics", "Embedded Systems"],
        "6": ["Natural Language Processing", "IoT", "Neural Networks"],
        "7": ["Reinforcement Learning", "Advanced Robotics", "AI Planning"],
        "8": ["Capstone Project", "Autonomous Systems", "AI Integration"]
    },
    "Mechanical Engineering": {
        "1": ["Engineering Math", "Physics 1", "Technical Drawing"],
        "2": ["Statics", "Math 2", "Material Science"],
        "3": ["Dynamics", "Thermodynamics 1", "Mechanics of Materials"],
        "4": ["Fluid Mechanics", "Thermodynamics 2", "Manufacturing Processes"],
        "5": ["Heat Transfer", "Machine Design", "Mechatronics"],
        "6": ["Control Systems", "Engineering Economics", "CAD/CAM"],
        "7": ["Robotics", "Energy Systems", "Project Management"],
        "8": ["Capstone Project", "Advanced Manufacturing", "Sustainable Design"]
    },
    "Chemical & Materials Engineering": {
        "1": ["Intro to Chemistry", "Math 1", "Physics 1"],
        "2": ["Organic Chemistry", "Math 2", "Material Properties"],
        "3": ["Thermodynamics", "Fluid Mechanics", "Heat Transfer"],
        "4": ["Chemical Kinetics", "Mass Transfer", "Instrumentation"],
        "5": ["Process Design", "Environmental Engineering", "Polymers"],
        "6": ["Nanomaterials", "Energy Systems", "Reaction Engineering"],
        "7": ["Advanced Materials", "Safety Engineering", "Project Management"],
        "8": ["Capstone Project", "Biochemical Engineering", "Sustainable Processes"]
    },
    "Applied Mathematics": {
        "1": ["Calculus 1", "Linear Algebra", "Introduction to Programming"],
        "2": ["Calculus 2", "Discrete Mathematics", "Statistics 1"],
        "3": ["Real Analysis", "Numerical Methods", "Probability"],
        "4": ["Differential Equations", "Complex Analysis", "Algebra"],
        "5": ["Mathematical Modelling", "Optimization", "Statistics 2"],
        "6": ["Computational Mathematics", "Graph Theory", "Machine Learning"],
        "7": ["Stochastic Processes", "Data Analysis", "Dynamical Systems"],
        "8": ["Capstone Project", "Advanced Modelling", "Big Data Analytics"]
    },
    "Economics & Data Science": {
        "1": ["Intro to Economics", "Math 1", "Intro to Programming"],
        "2": ["Microeconomics", "Statistics", "Math 2"],
        "3": ["Macroeconomics", "Data Analysis", "Econometrics"],
        "4": ["Machine Learning", "Python for Data Science", "Game Theory"],
        "5": ["Big Data", "Data Visualization", "Development Economics"],
        "6": ["Forecasting", "Time Series Analysis", "Behavioral Economics"],
        "7": ["AI in Economics", "Policy Analysis", "Deep Learning"],
        "8": ["Capstone Project", "Advanced Econometrics", "Data Ethics"]
    },
    "Pedagogy": {
        "1": ["Introduction to Education", "Psychology", "English 1"],
        "2": ["Child Development", "Sociology", "Teaching Skills"],
        "3": ["Curriculum Design", "Assessment Methods", "Philosophy of Education"],
        "4": ["Classroom Management", "Inclusive Education", "Educational Technology"],
        "5": ["Research in Education", "Language Teaching", "Mentoring"],
        "6": ["Educational Psychology", "Creative Pedagogy", "Global Perspectives"],
        "7": ["Leadership in Education", "Learning Theories", "Digital Learning"],
        "8": ["Capstone Project", "Policy & Reform", "Educational Innovation"]
    },
    "Industrial Management": {
        "1": ["Intro to Management", "Math 1", "Accounting Basics"],
        "2": ["Business Statistics", "Operations Management", "Economics"],
        "3": ["Project Management", "Logistics", "Marketing"],
        "4": ["Quality Control", "Financial Management", "HR Management"],
        "5": ["Production Systems", "Supply Chain", "Risk Management"],
        "6": ["Lean Management", "ERP Systems", "Industrial Safety"],
        "7": ["Strategic Management", "Innovation", "Data Analytics"],
        "8": ["Capstone Project", "Sustainability", "Industrial Automation"]
    }
}


def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_question_count():
    if os.path.exists(QUESTION_COUNT_FILE):
        with open(QUESTION_COUNT_FILE, 'r') as f:
            return json.load(f).get("count", 1)
    return 1

def save_question_count(count):
    with open(QUESTION_COUNT_FILE, 'w') as f:
        json.dump({"count": count}, f)

# ========== Handlers ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(major, callback_data=major)] for major in majors]
    await update.message.reply_text("Select your major:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_MAJOR

async def choose_major(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['major'] = query.data

    keyboard = [[InlineKeyboardButton(f"Semester {i}", callback_data=str(i))] for i in range(1, 9)]
    await query.edit_message_text("Select your current semester:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_SEMESTER

async def choose_semester(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    semester = query.data
    context.user_data['semester'] = semester

    user_id = str(query.from_user.id)
    user_info = load_user_data()
    user_info[user_id] = {
        "major": context.user_data['major'],
        "semester": semester
    }
    save_user_data(user_info)

    msg = f"📚 Your info:\nMajor: {context.user_data['major']}\nSemester: {semester}"
    sent_msg = await query.edit_message_text(msg)
    await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=sent_msg.message_id)
    return ConversationHandler.END



async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_info = load_user_data().get(user_id)
    if not user_info:
        await update.message.reply_text("Please use /start first to register your major and semester.")
        return

    major = user_info['major']
    semester = user_info['semester']
    classes = classes_by_major_semester.get(major, {}).get(semester, [])

    if not classes:
        await update.message.reply_text("No classes found for your selection. Contact admin to update class list.")
        return

    # Save question text
    context.user_data['pending_question'] = " ".join(context.args)

    # Check for image
    photo = update.message.photo
    if photo:
        # Telegram sends multiple sizes, pick the largest one
        context.user_data['pending_photo'] = photo[-1].file_id
    else:
        context.user_data['pending_photo'] = None

    # Class selection keyboard
    keyboard = [[InlineKeyboardButton(cls, callback_data=cls)] for cls in classes]
    keyboard.append([InlineKeyboardButton("Off-topic", callback_data="Off-topic")])
    await update.message.reply_text("Choose the class this question is for:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_CLASS



async def choose_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    class_name = query.data
    question_number = load_question_count()
    question = context.user_data.get('pending_question', '')
    photo_id = context.user_data.get('pending_photo')

    if class_name == "Off-topic":
        hashtag = "off_topic"
    else:
        hashtag = class_name.replace(" ", "_")

    caption = f"Q{question_number} #{hashtag}\n\n{question}"

    if photo_id:
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id, caption=caption)
    else:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=caption)

    await query.edit_message_text("✅ Your question was sent anonymously!")
    save_question_count(question_number + 1)
    return ConversationHandler.END

# ========== Main ==========

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_MAJOR: [CallbackQueryHandler(choose_major)],
            CHOOSING_SEMESTER: [CallbackQueryHandler(choose_semester)]
        },
        fallbacks=[]
    )

    ask_handler = ConversationHandler(
        entry_points=[CommandHandler('ask', ask)],
        states={
            CHOOSING_CLASS: [CallbackQueryHandler(choose_class)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(ask_handler)
    app.run_polling()
