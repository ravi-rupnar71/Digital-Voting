
CREATE TABLE IF NOT EXISTS admin (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,          
    email    TEXT
);


CREATE TABLE IF NOT EXISTS voters (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id  TEXT UNIQUE NOT NULL,
    name      TEXT NOT NULL,
    email     TEXT UNIQUE NOT NULL,
    password  TEXT NOT NULL,         -- stored as a hash, never plain text
    has_voted INTEGER NOT NULL DEFAULT 0
);

-- ---------- CANDIDATES 

CREATE TABLE IF NOT EXISTS candidates (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    party TEXT,
    email TEXT UNIQUE NOT NULL,
    votes INTEGER NOT NULL DEFAULT 0
);

-- ---------- VOTES ----------

CREATE TABLE IF NOT EXISTS votes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id     TEXT NOT NULL UNIQUE,
    candidate_id INTEGER NOT NULL,
    vote_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voter_id) REFERENCES voters(voter_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);



-- Sample admin login -> username: admin | password: admin123
INSERT OR IGNORE INTO admin (username, password, email) VALUES
('admin', 'scrypt:32768:8:1$ifJO8Y54w790tB7v$8d76e29f23ca4670eebdc921e01663e846ebd14dfd90d94641aacb7806d4b3c3e72fda5a959a134a1bbfc98dab53a89d66ac59fdfcc6503f9a368d3e89149757', 'admin@example.com');

-- Sample voters -> password for both: pass123
INSERT OR IGNORE INTO voters (voter_id, name, email, password) VALUES
('V001', 'Ravikant Rupnar', 'ravikant.v001@example.com', 'scrypt:32768:8:1$2eljxcEvYMXI8SyS$f1fc62d8774753b541e932db14afa32ac9ec818febbe3379708fe6ae6a2ebcbcb5871751ab3fafb6e8e908775c8a1e5f0d795912cb64c0cbc416437160fe79a7'),
('V002', 'Parth Chavan',    'parth.v002@example.com',    'scrypt:32768:8:1$2eljxcEvYMXI8SyS$f1fc62d8774753b541e932db14afa32ac9ec818febbe3379708fe6ae6a2ebcbcb5871751ab3fafb6e8e908775c8a1e5f0d795912cb64c0cbc416437160fe79a7');

-- Sample candidates
INSERT OR IGNORE INTO candidates (name, party, email) VALUES
('Candidate A', 'Party One', 'candidatea@example.com'),
('Candidate B', 'Party Two', 'candidateb@example.com');
