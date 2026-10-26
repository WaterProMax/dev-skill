PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(128) NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 128),
    isbn VARCHAR(20) NOT NULL CHECK (length(isbn) BETWEEN 10 AND 20),
    course_name VARCHAR(64) NULL DEFAULT NULL,
    seller_id VARCHAR(64) NOT NULL CHECK (length(trim(seller_id)) > 0),
    price_cents INTEGER NOT NULL CHECK (price_cents > 0),
    condition_level VARCHAR(16) NOT NULL DEFAULT 'GOOD' CHECK (condition_level IN ('NEW', 'LIKE_NEW', 'GOOD', 'ACCEPTABLE')),
    status VARCHAR(16) NOT NULL DEFAULT 'ON_SALE' CHECK (status IN ('ON_SALE', 'RESERVED', 'SOLD', 'OFF_SHELF')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
CREATE INDEX IF NOT EXISTS idx_books_seller ON books(seller_id);
CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(40) NOT NULL,
    book_id INTEGER NOT NULL,
    buyer_id VARCHAR(64) NOT NULL CHECK (length(trim(buyer_id)) > 0),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'CANCELLED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_order_no ON orders(order_no);
CREATE INDEX IF NOT EXISTS idx_orders_book_id ON orders(book_id);
CREATE UNIQUE INDEX IF NOT EXISTS uk_orders_active_book ON orders(book_id) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_orders_buyer_id ON orders(buyer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
