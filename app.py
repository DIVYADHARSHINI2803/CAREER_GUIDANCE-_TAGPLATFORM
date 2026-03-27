"""
TAG - Together Achieve Growth
Enhanced Version with Real-time Updates & Better UI/UX
"""

import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
from datetime import datetime
import time
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import hashlib
import os

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="TAG - Career Guidance",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
def load_css():
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 0rem 1rem;
        }
        
        /* Card styling */
        .css-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 1rem;
        }
        
        /* Statistic cards */
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        /* Success message animation */
        @keyframes slideIn {
            from {
                transform: translateY(-100%);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        .stAlert {
            animation: slideIn 0.5s ease-out;
        }
        
        /* Query card styling */
        .query-card {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            border-left: 5px solid #667eea;
        }
        
        /* Badge styling */
        .badge {
            display: inline-block;
            padding: 0.25rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-right: 0.5rem;
        }
        .badge-engineering { background: #ff6b6b; color: white; }
        .badge-medical { background: #4ecdc4; color: white; }
        .badge-arts { background: #ffd93d; color: black; }
        .badge-government { background: #6c5ce7; color: white; }
        .badge-other { background: #a8a8a8; color: white; }
        
        /* Typography */
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem !important;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Form styling */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s;
        }
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

# ==================== DATABASE SETUP ====================
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('database.db', check_same_thread=False)
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create queries table with status
    c.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            student_email TEXT NOT NULL,
            career_type TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_response TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create notifications table
    c.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if admin exists, if not create default admin
    c.execute("SELECT * FROM users WHERE role='admin'")
    if not c.fetchone():
        admin_password = hash_password("admin123")
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                 ("Admin", "admin@tag.com", admin_password, "admin"))
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# ==================== DATABASE OPERATIONS ====================
def create_user(name, email, password):
    """Create a new user in database"""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        if c.fetchone():
            return False, "Email already registered!"
        
        hashed = hash_password(password)
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                 (name, email, hashed))
        user_id = c.lastrowid
        
        # Create welcome notification
        c.execute("INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
                 (user_id, "Welcome to TAG! Start exploring career options.", "success"))
        
        conn.commit()
        return True, "Registration successful!"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def authenticate_user(email, password):
    """Authenticate user login"""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        
        if user and verify_password(password, user[3]):
            return True, {"id": user[0], "name": user[1], "email": user[2], "role": user[4]}
        return False, "Invalid email or password!"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def save_query(student_name, student_email, career_type, phone, message):
    """Save student query to database"""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO queries (student_name, student_email, career_type, phone, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_name, student_email, career_type, phone, message))
        
        # Get admin users for notification
        c.execute("SELECT id FROM users WHERE role='admin'")
        admins = c.fetchall()
        for admin in admins:
            c.execute('''
                INSERT INTO notifications (user_id, message, type) 
                VALUES (?, ?, ?)
            ''', (admin[0], f"New query from {student_name} regarding {career_type}", "info"))
        
        conn.commit()
        return True, "Query submitted successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def get_all_queries():
    """Retrieve all queries from database"""
    try:
        conn = sqlite3.connect('database.db')
        df = pd.read_sql_query("SELECT * FROM queries ORDER BY date DESC", conn)
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()

def get_student_queries(email):
    """Retrieve queries for specific student"""
    try:
        conn = sqlite3.connect('database.db')
        df = pd.read_sql_query("SELECT * FROM queries WHERE student_email=? ORDER BY date DESC", conn, params=(email,))
        return df
    except Exception as e:
        return pd.DataFrame()
    finally:
        conn.close()

def delete_query(query_id):
    """Delete a query from database"""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM queries WHERE id=?", (query_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def update_query_status(query_id, status, response=""):
    """Update query status and add admin response"""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            UPDATE queries 
            SET status=?, admin_response=? 
            WHERE id=?
        ''', (status, response, query_id))
        
        # Get student email for notification
        c.execute("SELECT student_email FROM queries WHERE id=?", (query_id,))
        student_email = c.fetchone()[0]
        c.execute("SELECT id FROM users WHERE email=?", (student_email,))
        student_id = c.fetchone()[0]
        
        # Notify student
        c.execute('''
            INSERT INTO notifications (user_id, message, type) 
            VALUES (?, ?, ?)
        ''', (student_id, f"Your query #{query_id} has been {status}", "success"))
        
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

def get_unread_notifications(user_id):
    """Get unread notifications for user"""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            SELECT * FROM notifications 
            WHERE user_id=? AND is_read=0 
            ORDER BY created_at DESC
        ''', (user_id,))
        notifications = c.fetchall()
        return notifications
    except Exception as e:
        return []
    finally:
        conn.close()

def mark_notifications_read(user_id):
    """Mark all notifications as read for user"""
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('UPDATE notifications SET is_read=1 WHERE user_id=?', (user_id,))
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()

# ==================== SESSION MANAGEMENT ====================
def init_session():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'Home'
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []

def logout():
    """Clear session and logout"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = 'Home'
    st.session_state.notifications = []
    st.rerun()

# ==================== UI COMPONENTS ====================
def notification_badge():
    """Display notification badge in sidebar"""
    if st.session_state.logged_in:
        notifications = get_unread_notifications(st.session_state.user['id'])
        if notifications:
            st.sidebar.markdown(f"""
                <div style="background-color: #ff4757; color: white; padding: 5px 10px; 
                            border-radius: 20px; text-align: center; margin: 10px 0;">
                    🔔 {len(notifications)} New Notification(s)
                </div>
            """, unsafe_allow_html=True)
            
            if st.sidebar.button("📩 View Notifications"):
                st.session_state.page = 'Notifications'
                st.rerun()

def get_badge_class(career_type):
    """Get CSS class for career type badge"""
    badges = {
        'Engineering': 'badge-engineering',
        'Medical': 'badge-medical',
        'Arts': 'badge-arts',
        'Government Jobs': 'badge-government',
        'Other': 'badge-other'
    }
    return badges.get(career_type, 'badge-other')

# ==================== UI PAGES ====================
def home_page():
    """Enhanced home page with animations and better UI"""
    load_css()
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
            <div style="padding: 2rem 0;">
                <h1 style="font-size: 4rem; margin-bottom: 0;">TAG</h1>
                <h2 style="color: #666; margin-top: 0;">Together Achieve Growth</h2>
                <p style="font-size: 1.2rem; color: #444; margin: 2rem 0;">
                    Empowering government school students with personalized career guidance 
                    to help them make informed decisions about their future.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.logged_in:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🚀 Get Started", use_container_width=True):
                    st.session_state.page = 'Sign Up'
                    st.rerun()
            with col2:
                if st.button("🔐 Login", use_container_width=True):
                    st.session_state.page = 'Login'
                    st.rerun()
    
    with col2:
        # Animated stats
        st.markdown("""
            <div class="css-card">
                <h3 style="color: white;">Platform Impact</h3>
                <h1 style="color: white; font-size: 3rem;">1000+</h1>
                <p>Students Guided</p>
                <h1 style="color: white; font-size: 3rem;">50+</h1>
                <p>Schools Reached</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Mission and Vision cards
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="stat-card">
                <h3 style="color: #667eea;">🎯 Our Mission</h3>
                <p style="color: #666; font-size: 1.1rem;">
                    To provide accessible career guidance to government school students, 
                    helping them discover their potential and make informed career choices.
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="stat-card">
                <h3 style="color: #667eea;">👁️ Our Vision</h3>
                <p style="color: #666; font-size: 1.1rem;">
                    Create a future where every government school student has access to 
                    quality career guidance, breaking barriers and enabling dreams.
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # Recent activities with better design
    st.markdown("---")
    st.markdown("## 📊 Recent Activities")
    
    activities = [
        {"icon": "🏫", "title": "Career Counseling Session", "location": "Govt. School, Delhi", "students": 50, "time": "2 hours ago"},
        {"icon": "📝", "title": "Engineering Career Workshop", "location": "Online Session", "students": 100, "time": "1 day ago"},
        {"icon": "🎓", "title": "Medical Entrance Guidance", "location": "Govt. School, Mumbai", "students": 25, "time": "2 days ago"},
        {"icon": "💼", "title": "Government Jobs Awareness", "location": "Govt. School, Chennai", "students": 75, "time": "3 days ago"},
    ]
    
    for activity in activities:
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        with col1:
            st.markdown(f"<h2>{activity['icon']}</h2>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{activity['title']}**")
            st.markdown(f"📍 {activity['location']}")
        with col3:
            st.markdown(f"👥 {activity['students']} students")
        with col4:
            st.markdown(f"🕐 {activity['time']}")
        st.markdown("---")

def signup_page():
    """Enhanced signup page"""
    load_css()
    st.markdown("<h1 style='text-align: center;'>Join TAG Community</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        with st.form("signup_form"):
            name = st.text_input("👤 Full Name *", placeholder="Enter your full name")
            email = st.text_input("📧 Email *", placeholder="Enter your email")
            password = st.text_input("🔒 Password *", type="password", placeholder="Min 6 characters")
            confirm_password = st.text_input("🔒 Confirm Password *", type="password", placeholder="Re-enter password")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
            
            if submitted:
                if not all([name, email, password, confirm_password]):
                    st.error("❌ Please fill all fields!")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match!")
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters long!")
                else:
                    with st.spinner("Creating your account..."):
                        time.sleep(1)  # Simulate processing
                        success, message = create_user(name, email, password)
                        if success:
                            st.success("✅ Account created successfully!")
                            st.balloons()
                            st.info("Please login to continue")
                            time.sleep(2)
                            st.session_state.page = 'Login'
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Login link
        st.markdown("""
            <div style="text-align: center; margin-top: 1rem;">
                Already have an account? <a href="#" onclick="alert('Click Login in sidebar')">Login here</a>
            </div>
        """, unsafe_allow_html=True)

def login_page():
    """Enhanced login page"""
    load_css()
    st.markdown("<h1 style='text-align: center;'>Welcome Back!</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("📧 Email *", placeholder="Enter your email")
            password = st.text_input("🔒 Password *", type="password", placeholder="Enter your password")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("🔐 Login", use_container_width=True)
            
            if submitted:
                if not all([email, password]):
                    st.error("❌ Please fill all fields!")
                else:
                    with st.spinner("Authenticating..."):
                        time.sleep(1)
                        success, result = authenticate_user(email, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = result
                            
                            if result['role'] == 'admin':
                                st.session_state.page = 'Admin'
                            else:
                                st.session_state.page = 'Dashboard'
                            
                            st.success(f"✨ Welcome back, {result['name']}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Demo credentials
        with st.expander("🔑 Demo Credentials"):
            st.markdown("""
                **Admin Access:**  
                - Email: `admin@tag.com`  
                - Password: `admin123`  
                
                **Student Access:**  
                - Create your own account or use any test account
            """)

def student_dashboard():
    """Enhanced student dashboard with real-time updates"""
    load_css()
    
    # Auto-refresh every 10 seconds for real-time updates
    count = st_autorefresh(interval=10000, key="student_refresh")
    
    # Welcome header with stats
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>👋 Welcome, {st.session_state.user['name']}!</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Get student's queries
    queries_df = get_student_queries(st.session_state.user['email'])
    
    # Statistics cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
            <div class="stat-card">
                <h3>📊 Total Queries</h3>
                <h2 style="color: #667eea;">{}</h2>
            </div>
        """.format(len(queries_df)), unsafe_allow_html=True)
    
    with col2:
        pending = len(queries_df[queries_df['status'] == 'pending']) if not queries_df.empty else 0
        st.markdown("""
            <div class="stat-card">
                <h3>⏳ Pending</h3>
                <h2 style="color: #ffa502;">{}</h2>
            </div>
        """.format(pending), unsafe_allow_html=True)
    
    with col3:
        answered = len(queries_df[queries_df['status'] == 'answered']) if not queries_df.empty else 0
        st.markdown("""
            <div class="stat-card">
                <h3>✅ Answered</h3>
                <h2 style="color: #26de81;">{}</h2>
            </div>
        """.format(answered), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="stat-card">
                <h3>📅 Joined</h3>
                <h2 style="color: #778ca3;">{}</h2>
            </div>
        """.format(datetime.now().strftime("%b %Y")), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Submit new query section
    with st.expander("📝 Submit New Career Query", expanded=True):
        st.markdown("""
            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                        padding: 1.5rem; border-radius: 15px;">
        """, unsafe_allow_html=True)
        
        with st.form("query_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                student_name = st.text_input("👤 Your Name *", value=st.session_state.user['name'])
                career_type = st.selectbox(
                    "🎯 Career Type *",
                    ["Engineering", "Medical", "Arts", "Government Jobs", "Other"]
                )
            
            with col2:
                phone = st.text_input("📞 Phone Number *", placeholder="10-digit mobile number")
                st.markdown("<br>", unsafe_allow_html=True)
            
            message = st.text_area("💬 Your Query *", placeholder="Describe your career query in detail...", height=150)
            
            submitted = st.form_submit_button("🚀 Submit Query", use_container_width=True)
            
            if submitted:
                if not all([student_name, career_type, phone, message]):
                    st.error("❌ Please fill all required fields!")
                elif len(phone) != 10 or not phone.isdigit():
                    st.error("❌ Please enter a valid 10-digit phone number!")
                else:
                    with st.spinner("Submitting your query..."):
                        success, msg = save_query(student_name, st.session_state.user['email'], career_type, phone, message)
                        if success:
                            st.success("✅ " + msg)
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ " + msg)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display previous queries with status
    st.markdown("## 📋 Your Query History")
    
    if queries_df.empty:
        st.info("🌟 You haven't submitted any queries yet. Use the form above to get started!")
    else:
        for _, row in queries_df.iterrows():
            # Status color
            status_color = {
                'pending': '#ffa502',
                'answered': '#26de81',
                'resolved': '#20bf6b'
            }.get(row['status'], '#778ca3')
            
            badge_class = get_badge_class(row['career_type'])
            
            st.markdown(f"""
                <div class="query-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span class="badge {badge_class}">{row['career_type']}</span>
                            <span class="badge" style="background-color: {status_color};">{row['status'].upper()}</span>
                        </div>
                        <small style="color: #999;">{row['date'][:10]}</small>
                    </div>
                    <p style="margin: 1rem 0; font-size: 1.1rem;">{row['message']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <small>📞 {row['phone']}</small>
                        <small>🆔 #{row['id']}</small>
                    </div>
            """, unsafe_allow_html=True)
            
            if row['admin_response']:
                st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                        <strong>👨‍🏫 Admin Response:</strong>
                        <p style="margin-top: 0.5rem;">{row['admin_response']}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

def admin_panel():
    """Enhanced admin panel with real-time updates"""
    load_css()
    
    # Auto-refresh every 5 seconds for real-time updates
    count = st_autorefresh(interval=5000, key="admin_refresh")
    
    # Header with refresh indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1>👑 Admin Dashboard</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style="background: #f0f2f6; padding: 0.5rem; border-radius: 10px; text-align: center;">
                <small>🔄 Auto-refresh: {datetime.now().strftime('%H:%M:%S')}</small>
            </div>
        """, unsafe_allow_html=True)
    
    # Get all queries
    queries_df = get_all_queries()
    
    # Statistics cards
    st.markdown("## 📊 Platform Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="stat-card">
                <h3>📝 Total Queries</h3>
                <h2 style="color: #667eea;">{}</h2>
            </div>
        """.format(len(queries_df)), unsafe_allow_html=True)
    
    with col2:
        pending = len(queries_df[queries_df['status'] == 'pending']) if not queries_df.empty else 0
        st.markdown("""
            <div class="stat-card">
                <h3>⏳ Pending</h3>
                <h2 style="color: #ffa502;">{}</h2>
            </div>
        """.format(pending), unsafe_allow_html=True)
    
    with col3:
        unique_students = queries_df['student_email'].nunique() if not queries_df.empty else 0
        st.markdown("""
            <div class="stat-card">
                <h3>👥 Active Students</h3>
                <h2 style="color: #26de81;">{}</h2>
            </div>
        """.format(unique_students), unsafe_allow_html=True)
    
    with col4:
        career_types = queries_df['career_type'].nunique() if not queries_df.empty else 0
        st.markdown("""
            <div class="stat-card">
                <h3>🎯 Career Fields</h3>
                <h2 style="color: #778ca3;">{}</h2>
            </div>
        """.format(career_types), unsafe_allow_html=True)
    
    # Charts section
    if not queries_df.empty:
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Career type distribution pie chart
            career_counts = queries_df['career_type'].value_counts().reset_index()
            career_counts.columns = ['Career Type', 'Count']
            
            fig = px.pie(career_counts, values='Count', names='Career Type', 
                        title='Career Type Distribution',
                        color_discrete_sequence=px.colors.sequential.Purples_r)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Queries over time
            queries_df['date_only'] = pd.to_datetime(queries_df['date']).dt.date
            daily_counts = queries_df.groupby('date_only').size().reset_index(name='count')
            
            fig = px.line(daily_counts, x='date_only', y='count', 
                         title='Daily Query Volume',
                         markers=True)
            fig.update_traces(line_color='#667eea')
            st.plotly_chart(fig, use_container_width=True)
    
    # Real-time queries table
    st.markdown("---")
    st.markdown("## 📋 Live Queries Feed")
    
    if queries_df.empty:
        st.info("📭 No queries in the database yet.")
    else:
        # Display each query as a card with admin actions
        for idx, row in queries_df.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                        <div style="background: white; padding: 1rem; border-radius: 10px; 
                                    border-left: 5px solid #667eea; margin-bottom: 1rem;">
                            <div style="display: flex; justify-content: space-between;">
                                <strong>👤 {row['student_name']}</strong>
                                <small>🕐 {row['date']}</small>
                            </div>
                            <p><strong>📧 Email:</strong> {row['student_email']}</p>
                            <p><strong>📞 Phone:</strong> {row['phone']}</p>
                            <p><strong>🎯 Career:</strong> {row['career_type']}</p>
                            <p><strong>💬 Message:</strong> {row['message']}</p>
                    """, unsafe_allow_html=True)
                    
                    if row['admin_response']:
                        st.markdown(f"""
                            <div style="background: #e8f4fd; padding: 0.5rem; border-radius: 5px;">
                                <strong>✅ Response:</strong> {row['admin_response']}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    # Status selector
                    current_status = row['status']
                    new_status = st.selectbox(
                        "Status",
                        ['pending', 'answered', 'resolved'],
                        index=['pending', 'answered', 'resolved'].index(current_status) if current_status in ['pending', 'answered', 'resolved'] else 0,
                        key=f"status_{row['id']}"
                    )
                    
                    # Response text area
                    response = st.text_area(
                        "Response",
                        value=row['admin_response'] if row['admin_response'] else "",
                        key=f"resp_{row['id']}",
                        height=100
                    )
                    
                    # Update button
                    if st.button("📤 Update", key=f"update_{row['id']}", use_container_width=True):
                        if update_query_status(row['id'], new_status, response):
                            st.success("✅ Updated!")
                            time.sleep(1)
                            st.rerun()
                    
                    # Delete button
                    if st.button("🗑️ Delete", key=f"del_{row['id']}", use_container_width=True):
                        if delete_query(row['id']):
                            st.success("✅ Deleted!")
                            time.sleep(1)
                            st.rerun()
                
                st.markdown("---")

def notifications_page():
    """Display notifications for user"""
    load_css()
    
    st.markdown("<h1>🔔 Notifications</h1>", unsafe_allow_html=True)
    
    notifications = get_unread_notifications(st.session_state.user['id'])
    
    if not notifications:
        st.info("📭 No new notifications")
    else:
        for notif in notifications:
            icon = {
                'info': '📌',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌'
            }.get(notif[4], '📌')
            
            st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 10px; 
                            margin-bottom: 1rem; border-left: 5px solid #667eea;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{icon} {notif[3]}</span>
                        <small>{notif[6]}</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("Mark all as read", use_container_width=True):
            mark_notifications_read(st.session_state.user['id'])
            st.success("✅ Notifications marked as read")
            time.sleep(1)
            st.rerun()

def about_page():
    """Enhanced about page"""
    load_css()
    
    st.markdown("<h1>ℹ️ About TAG</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="stat-card">
                <h3>🎯 Our Mission</h3>
                <p>To democratize career guidance for government school students across India, 
                ensuring every student has access to quality counseling and information about 
                various career paths.</p>
            </div>
            
            <div class="stat-card">
                <h3>👁️ Our Vision</h3>
                <p>A future where no student is left behind due to lack of guidance, and every 
                government school student can make informed career decisions.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="stat-card">
                <h3>🌟 What We Offer</h3>
                <ul style="list-style-type: none; padding-left: 0;">
                    <li>✓ Free career counseling</li>
                    <li>✓ Expert guidance</li>
                    <li>✓ Personalized queries</li>
                    <li>✓ Resource library</li>
                    <li>✓ Mentorship programs</li>
                </ul>
            </div>
            
            <div class="stat-card">
                <h3>📞 Contact Us</h3>
                <p>📧 Email: support@tagplatform.com</p>
                <p>📞 Phone: +91 1234567890</p>
                <p>🏢 Address: TAG Foundation, New Delhi</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Team section
    st.markdown("---")
    st.markdown("## 👥 Our Team")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div style="text-align: center;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            width: 100px; height: 100px; border-radius: 50%; margin: 0 auto; 
                            display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 2rem;">👩‍🏫</span>
                </div>
                <h4>Dr. Priya Sharma</h4>
                <p style="color: #666;">Founder & Director</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="text-align: center;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            width: 100px; height: 100px; border-radius: 50%; margin: 0 auto;
                            display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 2rem;">👨‍🔬</span>
                </div>
                <h4>Prof. Rajesh Kumar</h4>
                <p style="color: #666;">Career Counselor</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style="text-align: center;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            width: 100px; height: 100px; border-radius: 50%; margin: 0 auto;
                            display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 2rem;">👩‍💻</span>
                </div>
                <h4>Anjali Singh</h4>
                <p style="color: #666;">Technical Lead</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div style="text-align: center;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            width: 100px; height: 100px; border-radius: 50%; margin: 0 auto;
                            display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 2rem;">👨‍🏫</span>
                </div>
                <h4>Vikram Patel</h4>
                <p style="color: #666;">Student Mentor</p>
            </div>
        """, unsafe_allow_html=True)

# ==================== MAIN APP ====================
def main():
    """Main application controller"""
    
    # Initialize database and session
    init_database()
    init_session()
    
    # Sidebar navigation with enhanced UI
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 1rem;">
                <h1 style="color: white; margin: 0;">🎯 TAG</h1>
                <p style="color: rgba(255,255,255,0.8);">Together Achieve Growth</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation options
        menu_options = ['Home', 'About']
        
        if not st.session_state.logged_in:
            menu_options.extend(['Login', 'Sign Up'])
        else:
            if st.session_state.user['role'] == 'admin':
                menu_options.extend(['Admin', 'Notifications'])
            else:
                menu_options.extend(['Dashboard', 'Notifications'])
        
        # Page selection with icons
        page_icons = {
            'Home': '🏠',
            'About': 'ℹ️',
            'Login': '🔐',
            'Sign Up': '📝',
            'Dashboard': '📊',
            'Admin': '👑',
            'Notifications': '🔔'
        }
        
        for option in menu_options:
            icon = page_icons.get(option, '📌')
            if st.sidebar.button(f"{icon} {option}", key=f"nav_{option}", use_container_width=True):
                st.session_state.page = option
                st.rerun()
        
        # Show notification badge if logged in
        if st.session_state.logged_in:
            st.markdown("---")
            notification_badge()
            
            # User info
            st.markdown(f"""
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
                    <p style="color: white; margin: 0;">👤 Logged in as:</p>
                    <p style="color: white; font-weight: bold; margin: 0;">{st.session_state.user['name']}</p>
                    <p style="color: rgba(255,255,255,0.8); font-size: 0.8rem;">{st.session_state.user['role'].title()}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.sidebar.button("🚪 Logout", use_container_width=True):
                logout()
    
    # Page routing
    if st.session_state.page == 'Home':
        home_page()
    elif st.session_state.page == 'About':
        about_page()
    elif st.session_state.page == 'Login':
        if not st.session_state.logged_in:
            login_page()
        else:
            st.session_state.page = 'Dashboard' if st.session_state.user['role'] != 'admin' else 'Admin'
            st.rerun()
    elif st.session_state.page == 'Sign Up':
        if not st.session_state.logged_in:
            signup_page()
        else:
            st.session_state.page = 'Dashboard'
            st.rerun()
    elif st.session_state.page == 'Dashboard':
        if st.session_state.logged_in and st.session_state.user['role'] == 'student':
            student_dashboard()
        else:
            st.warning("Please login as student to access dashboard")
            st.session_state.page = 'Login'
            st.rerun()
    elif st.session_state.page == 'Admin':
        if st.session_state.logged_in and st.session_state.user['role'] == 'admin':
            admin_panel()
        else:
            st.warning("Unauthorized access! Please login as admin.")
            st.session_state.page = 'Login'
            st.rerun()
    elif st.session_state.page == 'Notifications':
        if st.session_state.logged_in:
            notifications_page()
        else:
            st.session_state.page = 'Login'
            st.rerun()

if __name__ == "__main__":
    main()