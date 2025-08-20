-- Table for the single user managing the events.
-- We'll assume a single user for this application, but designing it this way
-- allows for future expansion.
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    organization VARCHAR(255)
);

-- Table for event details.
CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    event_name VARCHAR(255) NOT NULL,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    location VARCHAR(255) NOT NULL,
    description TEXT
);

-- Table for different ticket types for each event.
CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(event_id),
    ticket_type VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    quantity_available INT NOT NULL,
    UNIQUE(event_id, ticket_type)
);

-- Table for attendees who register for an event.
CREATE TABLE attendees (
    attendee_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL
);

-- Junction table to record which attendee purchased which ticket.
-- This handles the M:N relationship between attendees and tickets.
CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    attendee_id INT NOT NULL REFERENCES attendees(attendee_id),
    ticket_id INT NOT NULL REFERENCES tickets(ticket_id),
    purchase_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantity_purchased INT NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL
);
