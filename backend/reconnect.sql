-- Database structure

CREATE TABLE users (
  username VARCHAR(50) PRIMARY KEY NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  person_details_id INTEGER,
  find_me BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  photo_path TEXT NOT NULL,
  relationship VARCHAR(255) NOT NULL CHECK(relationship != 'Not allow for users themselves'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  img1_id INTEGER,
  img2_id INTEGER,
  person_details_id1 INTEGER,
  person_details_id2 INTEGER,
  status VARCHAR(50) NOT NULL,
  match_score FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(img1_id) REFERENCES images(id),
  FOREIGN KEY(img2_id) REFERENCES images(id),
  FOREIGN KEY(person_details_id1) REFERENCES person_details(id),
  FOREIGN KEY(person_details_id2) REFERENCES person_details(id)
);
CREATE TABLE person_details (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  status BOOLEAN DEFAULT FALSE,
  username VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  age INTEGER NOT NULL,
  city INTEGER NOT NULL,
  biological_sex INTEGER NOT NULL CHECK(biological_sex IN (0, 1)),
  height INTEGER,
  distinguishing_marks VARCHAR,
  phone VARCHAR(255) NOT NULL,
  mail VARCHAR(255) NOT NULL,
  last_seen_year INTEGER,
  img_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(username) REFERENCES users(username),
  FOREIGN KEY(img_id) REFERENCES images(id)
);