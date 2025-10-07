-- Fix missing post_categories table
-- This script creates the missing blog-related tables

-- Create post_categories table
CREATE TABLE IF NOT EXISTS post_categories (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delete_at TIMESTAMP WITH TIME ZONE,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT
);

-- Create unique index on slug
CREATE UNIQUE INDEX IF NOT EXISTS ix_post_categories_slug ON post_categories (slug);

-- Create posts table
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delete_at TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    cover_image VARCHAR(255) NOT NULL DEFAULT '',
    summary VARCHAR(255) NOT NULL DEFAULT '',
    published_at TIMESTAMP,
    tags JSON NOT NULL DEFAULT '[]',
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES post_categories(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for posts table
CREATE UNIQUE INDEX IF NOT EXISTS ix_posts_slug ON posts (slug);
CREATE UNIQUE INDEX IF NOT EXISTS ix_posts_title ON posts (title);

-- Create post_sections table
CREATE TABLE IF NOT EXISTS post_sections (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    delete_at TIMESTAMP WITH TIME ZONE,
    title VARCHAR(255) NOT NULL,
    cover_image VARCHAR(255),
    content TEXT NOT NULL,
    section_style VARCHAR(255) DEFAULT '',
    position INTEGER NOT NULL DEFAULT 1,
    post_id INTEGER NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);
