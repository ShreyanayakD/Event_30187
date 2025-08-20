import psycopg2
import streamlit as st
import pandas as pd
import numpy as np

# Use st.cache_resource to create a single, persistent connection pool
@st.cache_resource(show_spinner=False)
def get_db_connection():
    """Establishes and caches a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="Event_Management",
            user="postgres",
            password="Nayak"
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Database connection failed: {e}")
        return None

def ensure_default_user_exists(user_id=1, name="Admin User", email="admin@example.com", organization="Event Management"):
    """
    Checks if a default user with the given user_id exists. If not, it creates one.
    This is necessary to satisfy the foreign key constraint for event creation.
    """
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
            user_exists = cur.fetchone()
            if not user_exists:
                # If not, create the default user
                cur.execute(
                    """
                    INSERT INTO users (user_id, name, email, organization)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (user_id, name, email, organization)
                )
                conn.commit()
                st.success(f"Default user created with ID {user_id}.")
            return True
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error ensuring default user exists: {error}")
        return False

# --- CRUD Operations ---

# CREATE
def create_event(user_id, event_name, event_date, event_time, location, description):
    """Creates a new event record."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events (user_id, event_name, event_date, event_time, location, description)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (user_id, event_name, event_date, event_time, location, description)
            )
            conn.commit()
            return True
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error creating event: {error}")
        return False

def create_ticket_type(event_id, ticket_type, price, quantity_available):
    """Creates a new ticket type for an event."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tickets (event_id, ticket_type, price, quantity_available)
                VALUES (%s, %s, %s, %s);
                """,
                (event_id, ticket_type, price, quantity_available)
            )
            conn.commit()
            return True
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error creating ticket type: {error}")
        return False

def register_attendee(name, email, ticket_id, quantity_purchased):
    """Registers an attendee and records a purchase."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            # Check if attendee exists, or create a new one
            cur.execute("SELECT attendee_id FROM attendees WHERE email = %s;", (email,))
            attendee_id = cur.fetchone()
            if attendee_id:
                attendee_id = attendee_id[0]
            else:
                cur.execute("INSERT INTO attendees (name, email) VALUES (%s, %s) RETURNING attendee_id;", (name, email))
                attendee_id = cur.fetchone()[0]

            # Get ticket price and calculate total
            cur.execute("SELECT price FROM tickets WHERE ticket_id = %s;", (ticket_id,))
            price = cur.fetchone()[0]
            total_price = price * quantity_purchased

            # Insert purchase record
            cur.execute(
                """
                INSERT INTO purchases (attendee_id, ticket_id, quantity_purchased, total_price)
                VALUES (%s, %s, %s, %s);
                """,
                (attendee_id, ticket_id, quantity_purchased, total_price)
            )
            conn.commit()
            return True
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error registering attendee: {error}")
        return False

# READ
def get_all_events():
    """Fetches all events from the database."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    try:
        df = pd.read_sql_query("SELECT * FROM events ORDER BY event_date DESC;", conn)
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error fetching events: {error}")
        return pd.DataFrame()

def get_attendees_by_event(event_id):
    """Fetches attendees for a specific event."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    try:
        query = """
        SELECT a.name, a.email, t.ticket_type, p.quantity_purchased, p.purchase_date
        FROM attendees a
        JOIN purchases p ON a.attendee_id = p.attendee_id
        JOIN tickets t ON p.ticket_id = t.ticket_id
        WHERE t.event_id = %s
        ORDER BY p.purchase_date;
        """
        # Convert event_id to a standard Python int
        event_id = int(event_id)
        df = pd.read_sql_query(query, conn, params=(event_id,))
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error fetching attendees: {error}")
        return pd.DataFrame()

# UPDATE
def update_event(event_id, event_name, event_date, event_time, location, description):
    """Updates an existing event record."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE events
                SET event_name = %s, event_date = %s, event_time = %s, location = %s, description = %s
                WHERE event_id = %s;
                """,
                (event_name, event_date, event_time, location, description, event_id)
            )
            conn.commit()
            return True
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error updating event: {error}")
        return False

# DELETE
def delete_event(event_id):
    """Deletes an event and associated tickets and purchases."""
    conn = get_db_connection()
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            # Delete related records first to maintain referential integrity
            cur.execute("DELETE FROM purchases WHERE ticket_id IN (SELECT ticket_id FROM tickets WHERE event_id = %s);", (event_id,))
            cur.execute("DELETE FROM tickets WHERE event_id = %s;", (event_id,))
            cur.execute("DELETE FROM events WHERE event_id = %s;", (event_id,))
            conn.commit()
            return True
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error deleting event: {error}")
        return False

# --- Business Insights ---
def get_event_dashboard_data(event_id):
    """Calculates and returns key business insights for a single event."""
    conn = get_db_connection()
    if conn is None: return None
    try:
        # Convert event_id to a standard Python int
        event_id = int(event_id)
        
        with conn.cursor() as cur:
            # Total tickets sold
            cur.execute("SELECT SUM(quantity_purchased) FROM purchases JOIN tickets USING (ticket_id) WHERE event_id = %s;", (event_id,))
            total_tickets_sold = cur.fetchone()[0] or 0

            # Total revenue generated
            cur.execute("SELECT SUM(total_price) FROM purchases JOIN tickets USING (ticket_id) WHERE event_id = %s;", (event_id,))
            total_revenue = cur.fetchone()[0] or 0.0

            # Get attendee count
            cur.execute("SELECT COUNT(DISTINCT attendee_id) FROM purchases JOIN tickets USING (ticket_id) WHERE event_id = %s;", (event_id,))
            attendee_count = cur.fetchone()[0] or 0

            # Ticket sales per type
            cur.execute("SELECT ticket_type, SUM(quantity_purchased) as tickets_sold FROM purchases JOIN tickets USING (ticket_id) WHERE event_id = %s GROUP BY ticket_type;", (event_id,))
            tickets_by_type = cur.fetchall()
            
            # Purchase value statistics
            cur.execute("SELECT AVG(total_price), MIN(total_price), MAX(total_price) FROM purchases JOIN tickets USING (ticket_id) WHERE event_id = %s;", (event_id,))
            avg_min_max_revenue = cur.fetchone()

            return {
                "total_tickets_sold": total_tickets_sold,
                "total_revenue": total_revenue,
                "attendee_count": attendee_count,
                "tickets_by_type": tickets_by_type,
                "avg_revenue": avg_min_max_revenue[0],
                "min_revenue": avg_min_max_revenue[1],
                "max_revenue": avg_min_max_revenue[2]
            }
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error fetching dashboard data: {error}")
        return None

def get_ticket_types(event_id):
    """Fetches all ticket types for a specific event."""
    conn = get_db_connection()
    if conn is None: return pd.DataFrame()
    try:
        # Convert event_id to a standard Python int
        event_id = int(event_id)
        query = "SELECT ticket_id, ticket_type, price, quantity_available FROM tickets WHERE event_id = %s;"
        df = pd.read_sql_query(query, conn, params=(event_id,))
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        st.error(f"Error fetching ticket types: {error}")
        return pd.DataFrame()