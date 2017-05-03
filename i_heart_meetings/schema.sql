--drop table if exists meetings;
--create table meetings (
--    meeting_id text primary key,
--    meeting_number integer,
--    summary text,
--    start text,
--    end text,
--    meeting_duration text,
--    num_attendees integer,
--    financial_cost_single_meeting text,
--    time_cost_single_days text,
--    time_cost_single_hours text,
--    time_cost_single_minutes text,
--    time_cost_single_seconds text
--);
drop table if exists entries;
create table entries (
    id integer primary key autoincrement,
    title text not null,
    'text' text not null
);
