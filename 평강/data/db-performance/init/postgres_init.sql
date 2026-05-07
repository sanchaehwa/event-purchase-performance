CREATE TABLE IF NOT EXISTS products (
    id            SERIAL         PRIMARY KEY,
    product_name  VARCHAR(500)   NOT NULL,
    brand         VARCHAR(200)   NOT NULL,
    category      VARCHAR(100),
    sub_category  VARCHAR(100),
    price         INT            NOT NULL,
    discount_rate INT,
    rating        DECIMAL(5,2),
    review_count  INT,
    tags          TEXT,
    description   TEXT,
    image_url     TEXT,
    source        VARCHAR(50),
    source_url    TEXT
);
