CREATE TABLE IF NOT EXISTS carpets(
    carpet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price INTEGER,
    country TEXT,
    composition TEXT,
    density INTEGER,
    height_pile FLOAT,
    provider TEXT);
CREATE TABLE IF NOT EXISTS images(
    images_id INTEGER PRIMARY KEY AUTOINCREMENT,
    image TEXT);
CREATE TABLE IF NOT EXISTS carpet_sizes(
    carpet_sizes_id INTEGER PRIMARY KEY AUTOINCREMENT,
    carpet_size TEXT);
CREATE TABLE IF NOT EXISTS c_sizes(
    c_sizes_id INTEGER PRIMARY KEY AUTOINCREMENT,
    carpet_id INTEGER,
    c_size TEXT,
    FOREIGN KEY (carpet_id) REFERENCES carpets (carpet_id),
    FOREIGN KEY (c_sizes_id) REFERENCES carpet_sizes (carpet_sizes_id));
CREATE TABLE IF NOT EXISTS t_images(
    t_image_id INTEGER PRIMARY KEY AUTOINCREMENT,
    carpet_id INTEGER,
    t_image TEXT,
    FOREIGN KEY (carpet_id) REFERENCES carpets (carpet_id),
    FOREIGN KEY (t_image_id) REFERENCES images (images_id));
CREATE TABLE IF NOT EXISTS avalon_carpets_links(
    avalon_carpet_links_id INTEGER PRIMARY KEY AUTOINCREMENT,
    carpet_link TEXT);
CREATE TABLE IF NOT EXISTS venera_carpets_links(
    venera_carpet_links_id INTEGER PRIMARY KEY AUTOINCREMENT,
    carpet_link TEXT);

SELECT COUNT(carpet_id) FROM carpets WHERE provider = 'Avalon' AND price != 0
