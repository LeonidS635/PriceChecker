CREATE TABLE IF NOT EXISTS credentials (
    user_id BIGINT NOT NULL,
    site_id BIGINT NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    PRIMARY KEY (user_id, site_id)
);
