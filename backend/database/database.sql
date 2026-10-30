CREATE DATABASE IF NOT EXISTS local_business_directory
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE local_business_directory;

CREATE TABLE IF NOT EXISTS users(
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL,
 email VARCHAR(150) NOT NULL UNIQUE,
 password VARCHAR(255) NOT NULL,
 phone VARCHAR(30),
 role ENUM("user","business_owner","admin") DEFAULT "user",
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories(
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL UNIQUE,
 image VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS businesses(
 id INT AUTO_INCREMENT PRIMARY KEY,
 owner_id INT NOT NULL,
 category_id INT NOT NULL,
 business_name VARCHAR(180) NOT NULL,
 description TEXT,
 address TEXT,
 location VARCHAR(150),
 phone VARCHAR(30),
 email VARCHAR(150),
 opening_time TIME,
 closing_time TIME,
 services TEXT,
 status ENUM("pending","approved","rejected") DEFAULT "pending",
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS business_images(
 id INT AUTO_INCREMENT PRIMARY KEY,
 business_id INT NOT NULL,
 image_path VARCHAR(500) NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(business_id) REFERENCES businesses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews(
 id INT AUTO_INCREMENT PRIMARY KEY,
 business_id INT NOT NULL,
 user_id INT NOT NULL,
 rating TINYINT NOT NULL,
 review_text TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(business_id) REFERENCES businesses(id) ON DELETE CASCADE,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 UNIQUE KEY one_review_per_user(user_id,business_id)
);

CREATE TABLE IF NOT EXISTS messages(
 id INT AUTO_INCREMENT PRIMARY KEY,
 sender_id INT NULL,
 business_id INT NULL,
 name VARCHAR(100) NOT NULL,
 email VARCHAR(150) NOT NULL,
 subject VARCHAR(200) NOT NULL,
 message TEXT NOT NULL,
 status ENUM("unread","read","replied") DEFAULT "unread",
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE SET NULL,
 FOREIGN KEY(business_id) REFERENCES businesses(id) ON DELETE SET NULL
);

INSERT IGNORE INTO categories(name) VALUES
("Restaurants"),("Hospitals"),("Grocery Stores"),("Salons"),
("Hotels"),("Medical Shops"),("Electronics");
