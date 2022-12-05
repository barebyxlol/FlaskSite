drop table if exists users;
create table users (
    id integer primary key autoincrement,
    username text not null,
    password text not null,
    name text,
    surname text,
    last_name text
);

drop table if exists resumes;
create table resumes (
    id integer primary key autoincrement,
    user_id integer not null,
    title text not null,
    employer text not null,
    experience text,
    skills text,
    relevant_info text,
    foreign key (user_id) references users(id)
);

