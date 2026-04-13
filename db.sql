
DROP TABLE IF EXISTS contacts;
CREATE TABLE contacts (
  id SERIAL PRIMARY KEY,
  name TEXT,
  phone TEXT NOT NULL,
  age INTEGER,
  city TEXT,
  state TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (phone)
);


DROP TABLE IF EXISTS templates;
CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


DROP TABLE IF EXISTS messages;
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  contact_id INTEGER NOT NULL,
  template_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
  UNIQUE (contact_id, template_id, status)
);
