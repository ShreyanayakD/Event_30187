import streamlit as st
import pandas as pd
from backend_em import (
    create_event, create_ticket_type, register_attendee, 
    get_all_events, get_attendees_by_event,
    update_event, delete_event, get_event_dashboard_data,
    get_ticket_types, ensure_default_user_exists
)

st.title("Event Management System 🗓️")
st.markdown("##### Name: Shreya D")
st.markdown("##### Roll No: 30187")

# A simple user_id for the single user.
USER_ID = 1

# Ensure the default user exists at the start of the app
if not ensure_default_user_exists(user_id=USER_ID):
    st.stop() # Stop the app if the user creation failed

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Manage Events", "Register Attendees"])
st.sidebar.markdown("---")
st.sidebar.write("👤 User: Admin")

# --- Main Content ---

if page == "Dashboard":
    st.header("Event Dashboard & Analytics 📊")
    
    events_df = get_all_events()
    if not events_df.empty:
        event_names = events_df['event_name'].tolist()
        selected_event_name = st.selectbox("Select an event:", event_names, index=0)
        
        # Convert to a standard Python int to avoid numpy error
        selected_event_id = int(events_df[events_df['event_name'] == selected_event_name]['event_id'].iloc[0])
        
        dashboard_data = get_event_dashboard_data(selected_event_id)
        if dashboard_data:
            st.subheader("Key Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Tickets Sold", dashboard_data['total_tickets_sold'])
            col2.metric("Total Revenue", f"${dashboard_data['total_revenue']:.2f}")
            col3.metric("Total Attendees", dashboard_data['attendee_count'])
            
            st.subheader("Ticket Sales Breakdown")
            tickets_by_type_df = pd.DataFrame(dashboard_data['tickets_by_type'], columns=['Ticket Type', 'Tickets Sold'])
            st.bar_chart(tickets_by_type_df.set_index('Ticket Type'))

            st.subheader("Purchase Analytics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Purchase", f"${dashboard_data['avg_revenue']:.2f}" if dashboard_data['avg_revenue'] else "$0.00")
            col2.metric("Minimum Purchase", f"${dashboard_data['min_revenue']:.2f}" if dashboard_data['min_revenue'] else "$0.00")
            col3.metric("Maximum Purchase", f"${dashboard_data['max_revenue']:.2f}" if dashboard_data['max_revenue'] else "$0.00")

            st.subheader("Registered Attendees")
            attendees_df = get_attendees_by_event(selected_event_id)
            if not attendees_df.empty:
                st.dataframe(attendees_df, use_container_width=True)
            else:
                st.info("No attendees have registered for this event yet.")
        else:
            st.warning("No dashboard data available for the selected event.")
    else:
        st.info("Please create an event first in the 'Manage Events' section.")

elif page == "Manage Events":
    st.header("Manage Your Events 🗓️")
    
    st.markdown("### Create New Event")
    with st.form("event_creation_form"):
        event_name = st.text_input("Event Name", placeholder="e.g., Tech Summit 2025")
        event_date = st.date_input("Date")
        event_time = st.time_input("Time")
        location = st.text_input("Location", placeholder="e.g., Conference Hall A")
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Create Event")
        if submitted:
            if create_event(USER_ID, event_name, event_date, event_time, location, description):
                st.success("Event created successfully!")
                st.rerun()
            else:
                st.error("Failed to create event.")
    
    st.markdown("---")
    st.markdown("### View and Update Existing Events")
    
    events_df = get_all_events()
    if not events_df.empty:
        events_df = events_df.rename(columns={
            'event_id': 'ID', 'event_name': 'Event Name', 'event_date': 'Date',
            'event_time': 'Time', 'location': 'Location', 'description': 'Description'
        })
        st.dataframe(events_df, use_container_width=True)
        
        selected_event_id = st.selectbox("Select Event ID to update or delete:", events_df['ID'].tolist())

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Delete Selected Event", use_container_width=True):
                if delete_event(selected_event_id):
                    st.success(f"Event {selected_event_id} and all related data deleted successfully.")
                    st.rerun()
                else:
                    st.error("Failed to delete event.")
        
        with col2:
            if st.button("Update Selected Event", use_container_width=True):
                st.session_state.update_mode_id = selected_event_id
                st.rerun()

        if 'update_mode_id' in st.session_state and st.session_state.update_mode_id:
            st.subheader("Update Event Details")
            event_to_update = events_df[events_df['ID'] == st.session_state.update_mode_id].iloc[0]
            
            with st.form("event_update_form"):
                new_event_name = st.text_input("Event Name", value=event_to_update['Event Name'])
                new_event_date = st.date_input("Date", value=event_to_update['Date'])
                new_event_time = st.time_input("Time", value=event_to_update['Time'])
                new_location = st.text_input("Location", value=event_to_update['Location'])
                new_description = st.text_area("Description", value=event_to_update['Description'])
                
                update_submitted = st.form_submit_button("Submit Update")
                if update_submitted:
                    if update_event(st.session_state.update_mode_id, new_event_name, new_event_date, new_event_time, new_location, new_description):
                        st.success("Event updated successfully!")
                        st.session_state.update_mode_id = None
                        st.rerun()
                    else:
                        st.error("Failed to update event.")
    else:
        st.info("No events created yet.")

elif page == "Register Attendees":
    st.header("Register Attendees & Sell Tickets 🎟️")
    
    events_df = get_all_events()
    if not events_df.empty:
        event_names = events_df['event_name'].tolist()
        selected_event_name = st.selectbox("Select an event:", event_names, index=0)
        
        # Convert to a standard Python int to avoid numpy error
        selected_event_id = int(events_df[events_df['event_name'] == selected_event_name]['event_id'].iloc[0])
        
        st.markdown("### Add a new ticket type")
        with st.form("ticket_creation_form"):
            ticket_type = st.text_input("Ticket Type", placeholder="e.g., General, VIP")
            price = st.number_input("Price", min_value=0.01, step=0.01, format="%.2f")
            quantity = st.number_input("Quantity Available", min_value=1, step=1)
            ticket_submitted = st.form_submit_button("Add Ticket Type")
            if ticket_submitted:
                if create_ticket_type(selected_event_id, ticket_type, price, quantity):
                    st.success("Ticket type added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add ticket type.")
        
        st.markdown("---")
        st.markdown("### Register an Attendee")
        
        tickets_df = get_ticket_types(selected_event_id)
        if not tickets_df.empty:
            with st.form("attendee_registration_form"):
                attendee_name = st.text_input("Attendee Name", placeholder="John Doe")
                attendee_email = st.text_input("Attendee Email", placeholder="john.doe@example.com")
                
                ticket_options = dict(zip(tickets_df['ticket_type'] + ' - $' + tickets_df['price'].astype(str), tickets_df['ticket_id']))
                selected_ticket_option = st.selectbox("Select Ticket Type:", list(ticket_options.keys()))
                selected_ticket_id = ticket_options[selected_ticket_option]
                
                quantity_to_purchase = st.number_input("Quantity to purchase", min_value=1, step=1)
                
                purchase_submitted = st.form_submit_button("Complete Registration")
                if purchase_submitted:
                    if register_attendee(attendee_name, attendee_email, selected_ticket_id, quantity_to_purchase):
                        st.success("Registration successful!")
                    else:
                        st.error("Failed to register attendee.")
        else:
            st.info("No ticket types available for this event. Please create one above.")